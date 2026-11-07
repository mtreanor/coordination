import json
from pathlib import Path

import pytest

from coordination.agents import RandomChooser
from coordination.config import RunConfig
from coordination.run import Run
from coordination.situation import Situation
from coordination.social import NoSocial
from coordination.work import InvestmentClubWork, WorkEvent

AGENTS = ["ana", "bo", "cy"]


def pick(decision, label):
    return next(o.id for o in decision.options if o.label == label)


def play_round(work, invest, payback, returns):
    """invest: agent -> label; payback: decision key -> label; returns fixes the dice."""
    work.next_round()
    work.returns = dict(returns)
    decisions = {d.key: d for d in work.decisions()}
    events = work.resolve({f"invest:{a}": pick(decisions[f"invest:{a}"], label) for a, label in invest.items()})
    decisions = {d.key: d for d in work.decisions()}
    assert set(decisions) == set(payback)
    events += work.resolve({key: pick(decisions[key], label) for key, label in payback.items()})
    return events


def test_round_one_of_the_worked_example():
    # docs/investment-club.md, round 1: Bo skims a x5, Cy returns everything on a x1.
    work = InvestmentClubWork(AGENTS)
    events = play_round(
        work,
        invest={"ana": "Invest 10 coins in bo", "bo": "Invest 5 coins in cy", "cy": "Invest 5 coins in ana"},
        payback={"payback:bo:ana": "Send back 17 coins to ana (a third)",
                 "payback:cy:bo": "Send back 5 coins to bo (all of it)",
                 "payback:ana:cy": "Send back 8 coins to cy (half)"},
        returns={"ana": 3, "bo": 5, "cy": 1},
    )
    assert work.scores() == {"ana": 17 + 7, "bo": 5 + 5 + 33, "cy": 5 + 8}
    assert work.decisions() == []
    invested = [(e.actor, e.target, e.changes) for e in events if e.kind == "invested in"]
    assert invested == [("ana", "bo", {"ana": {"coins": -10}, "bo": {"coins": 10}}),
                        ("bo", "cy", {"bo": {"coins": -5}, "cy": {"coins": 5}}),
                        ("cy", "ana", {"cy": {"coins": -5}, "ana": {"coins": 5}})]
    paid = {(e.actor, e.target): e for e in events if e.kind == "paid back"}
    assert paid[("bo", "ana")].changes == {"bo": {"coins": -17}, "ana": {"coins": 17}}
    assert paid[("bo", "ana")].details == {"amount": 17, "stake": 10}
    assert all(e.credit == "witnesses" for e in events)
    assert all(set(e.witnesses) == {e.actor, e.target} for e in events)
    # The investor learns what came back, never the project's return.
    assert "bo sent back 17 coins on your 10." in work.briefing("ana")
    assert "x5" not in work.briefing("ana").split("Your past rounds:")[1]  # bo's return
    assert "Your project returned x5" in work.briefing("bo")
    # Ground truth is in the record, for the log only.
    assert work.record()["returns"] == {"ana": 3, "bo": 5, "cy": 1}
    assert all(f.name == "points" for f in work.state())


def test_nobody_invests_ends_the_round_without_a_payback_step():
    work = InvestmentClubWork(AGENTS, rounds=1)
    work.next_round()
    keys = [d.key for d in work.decisions()]
    events = work.resolve({key: 0 for key in keys})  # option 0 keeps everything
    assert events == [] and work.decisions() == []
    assert work.scores() == {a: 10 for a in AGENTS}
    assert "Nobody invested in you." in work.briefing("ana")
    assert work.over()


def test_a_pass_keeps_everything_and_sends_nothing_back():
    work = InvestmentClubWork(AGENTS)
    work.next_round()
    work.returns = {"ana": 3, "bo": 3, "cy": 3}
    decisions = {d.key: d for d in work.decisions()}
    work.resolve({"invest:ana": pick(decisions["invest:ana"], "Invest 10 coins in bo"),
                  "invest:bo": None, "invest:cy": 0})
    events = work.resolve({"payback:bo:ana": None})
    assert work.scores() == {"ana": 0, "bo": 10 + 30, "cy": 10}
    assert events[0].details == {"amount": 0, "stake": 10}
    assert events[0].changes == {"bo": {"coins": 0}, "ana": {"coins": 0}}


def test_payback_menu_has_no_duplicate_amounts():
    work = InvestmentClubWork(AGENTS)
    work.next_round()
    work.returns = {"ana": 1, "bo": 1, "cy": 1}
    decisions = {d.key: d for d in work.decisions()}
    work.resolve({"invest:ana": pick(decisions["invest:ana"], "Invest 5 coins in bo"), "invest:bo": 0, "invest:cy": 0})
    labels = [o.label for o in work.decisions()[0].options]
    amounts = [int(label.split()[2]) for label in labels]
    assert amounts == sorted(set(amounts)) == [0, 2, 3, 5]


def test_dice_follow_the_seed():
    rolls = []
    for _ in range(2):
        work = InvestmentClubWork(AGENTS, seed=7)
        work.next_round()
        rolls.append(work.returns)
    assert rolls[0] == rolls[1]


def test_events_name_only_their_witnesses_and_hide_uncredited_actors():
    with pytest.raises(ValueError, match="aren't witnesses"):
        WorkEvent(kind="x", actor="ana", target="bo", witnesses=["ana", "bo"], changes={"cy": {"coins": -1}})
    with pytest.raises(ValueError, match="needs text"):
        WorkEvent(kind="x", actor="ana", witnesses=["ana", "bo"], credit="none")


def test_a_full_run_plays_both_steps_and_logs_ground_truth(tmp_path):
    work = InvestmentClubWork(AGENTS, rounds=2)
    choosers = {agent: RandomChooser(i) for i, agent in enumerate(AGENTS)}
    Run(work, NoSocial(), choosers, Situation(name="t"), tmp_path).play()
    rounds = [json.loads(line) for line in (tmp_path / "rounds.jsonl").read_text().splitlines()]
    assert [r["work"]["round"] for r in rounds] == [1, 2]
    assert rounds[-1]["work"]["coins"] == rounds[-1]["scores"]
    decisions = [json.loads(line) for line in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    assert len([d for d in decisions if "Choose your investment" in d["request"]["briefing"]]) == 6


def test_run_config_builds_the_parts(tmp_path):
    (tmp_path / "club.toml").write_text(
        'work = "investment-club"\nagents = ["ana", "bo", "cy"]\nrounds = 2\n'
        '[social]\nlayer = "off"\n[choosers]\ndefault = "random"\nbo = "rue"\n')
    config = RunConfig.load(tmp_path / "club.toml")
    work = config.make_work()
    assert work.agents == AGENTS and work.rounds == 2
    assert isinstance(config.make_social(), NoSocial)
    assert config.chooser_names(work.agents) == {"ana": "random", "bo": "rue", "cy": "random"}
    manifest = config.manifest(work.agents)
    assert manifest["work"] == "investment-club" and "commit" in manifest


def test_run_config_rejects_unknown_agents(tmp_path):
    config = RunConfig(work="investment-club", agents=AGENTS, choosers={"default": "random", "dave": "rue"})
    with pytest.raises(SystemExit, match="dave"):
        config.chooser_names(AGENTS)
    (tmp_path / "s.toml").write_text('[principals]\ndave = "Be selfish."\n')
    with pytest.raises(SystemExit, match="dave"):
        RunConfig(situation="s").load_situation(AGENTS, tmp_path)


def test_checked_in_configs_load_and_match_their_rue_scenarios():
    paths = sorted(Path("configs").glob("*.toml"))
    assert paths
    for path in paths:
        config = RunConfig.load(path)
        work = config.make_work()
        config.load_situation(work.agents)
        config.chooser_names(work.agents)
        config.check_cast(work.agents)  # the RUE scenario declares exactly these agents


def test_cast_check_names_what_to_change(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "entities.json").write_text('{"agent": {"privateStore": true, "ana": {}, "zed": {}}}')
    (tmp_path / "project.config.json").write_text('{"scenarios": {"s": "s"}}')
    config = RunConfig(work="investment-club", agents=AGENTS, social={"layer": "rue", "scenario": "s"})
    with pytest.raises(SystemExit, match=r"Add to its \"agent\" entities: \['bo', 'cy'\][\s\S]*Drop from it[\s\S]*\['zed'\]"):
        config.check_cast(AGENTS, tmp_path / "project.config.json")
    RunConfig(social={"layer": "off"}).check_cast(AGENTS, tmp_path / "project.config.json")  # work-only: no check


def test_investment_menus_are_shuffled_by_the_seed():
    def first_targets(seed):
        work = InvestmentClubWork(seed=seed)
        orders = []
        for _ in range(3):
            work.next_round()
            orders += [d.options[1].label for d in work.decisions()]
            work.resolve({})  # everyone passes: keeps everything, round ends
        return orders
    assert first_targets(1) == first_targets(1)
    assert len(set(first_targets(1))) > 3  # not always the same business listed first


def test_one_config_switches_works_by_name():
    config = RunConfig.load("configs/pilot.toml")
    for name in ["investment-club", "not-my-bug"]:
        switched = config.model_copy(update={"work": name})
        work = switched.make_work()
        assert work.name == name and work.agents == config.agents
        switched.load_situation(work.agents)
        switched.check_cast(work.agents)
