import json
from pathlib import Path

import httpx
import pytest

from coordination.agents import RandomChooser
from coordination.run import Run
from coordination.situation import Situation
from coordination.social import NoSocial, RueSocial
from coordination.work import StubWork, WorkEvent

AGENTS = ["alice", "bob", "carol", "dave"]


def test_stub_work_moves_and_witnesses():
    work = StubWork(AGENTS, rounds=1)
    work.next_round()
    menus = {d.agent: d.options for d in work.decisions()}
    pick = lambda agent, label: next(o.id for o in menus[agent] if o.label == label)
    events = work.resolve({
        "alice": pick("alice", "Take from bob"),
        "bob": pick("bob", "Help carol"),
        "carol": pick("carol", "Do your own work"),
        "dave": None,
    })
    assert work.scores() == {"alice": 2, "bob": -2, "carol": 3, "dave": 0}
    assert [(e.kind, e.actor, e.target, e.witnesses) for e in events] == [
        ("took from", "alice", "bob", ["alice", "bob"]),
        ("helped", "bob", "carol", ["bob", "carol"]),
    ]
    assert [e.changes for e in events] == [{"alice": {"points": 2}, "bob": {"points": -2}}, {"carol": {"points": 2}}]
    assert "alice took 2 points from you." in work.briefing("bob")
    assert "alice" not in work.briefing("dave").split("In the last round:")[1]
    assert work.decisions() == []
    assert work.over()


class RecordingSocial(NoSocial):
    name = "recording"

    def __init__(self):
        self.calls = []

    def start(self, agents, facts):
        self.calls.append(("start", tuple(facts)))

    def briefing(self, agent):
        return "- You like everyone 5 out of 10."

    def mirror(self, state):
        self.calls.append(("mirror", tuple((f.name, *f.args, f.value) for f in state)))

    def social_round(self, events, ask):
        self.calls.append(("social_round", len(events)))


def test_run_sequences_phases_and_logs(tmp_path):
    social = RecordingSocial()
    situation = Situation(name="t", facts=["alice.likes(alice, bob) = 1"])
    choosers = {agent: RandomChooser(i) for i, agent in enumerate(AGENTS)}
    run = Run(StubWork(AGENTS, rounds=2), social, choosers, situation, tmp_path)
    scores = run.play()

    assert set(scores) == set(AGENTS)
    assert social.calls[0] == ("start", ("alice.likes(alice, bob) = 1",))
    steps = [c if isinstance(c, str) else c[0] for c in social.calls[1:]]
    assert steps == ["mirror", "social_round"] * 2
    mirrored = dict((name_agent[1], name_agent[2]) for name_agent in social.calls[-2][1])
    assert mirrored == scores
    records = [json.loads(line) for line in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    assert len(records) == 8 and {r["phase"] for r in records} == {"work"}
    briefing = records[0]["request"]["briefing"]
    assert "The work:" in briefing and "What you believe about your colleagues:" in briefing
    assert len((tmp_path / "rounds.jsonl").read_text().splitlines()) == 2


def test_work_only_briefing_has_no_social_section(tmp_path):
    run = Run(StubWork(AGENTS), NoSocial(), {}, Situation(name="t"), tmp_path)
    assert "What you believe" not in run.briefing("alice", "work", "Choose.")


def test_situation_loads_principal_instructions(tmp_path):
    (tmp_path / "s.toml").write_text('facts = ["x"]\n[principals]\nbob = "Be selfish."\n')
    situation = Situation.load("s", tmp_path)
    assert situation.facts == ["x"]
    assert situation.instructions_for("bob") == "Be selfish."
    assert situation.instructions_for("alice") == situation.instructions


def rue_server_up() -> bool:
    try:
        httpx.get("http://localhost:5174/api/play/social-layer-data/session", timeout=1)
        return True
    except httpx.HTTPError:
        return False


def play_rue(tmp_path, **social_options):
    choosers = {agent: RandomChooser(i) for i, agent in enumerate(AGENTS)}
    work = StubWork(AGENTS, rounds=2)
    social = RueSocial("social-layer-data", **social_options)
    run = Run(work, social, choosers, Situation(name="t", facts=["alice.likes(alice, bob) = 1"]), tmp_path)
    run.play()
    phases = {json.loads(line)["phase"] for line in (tmp_path / "decisions.jsonl").read_text().splitlines()}
    return work, social, phases


needs_rue = pytest.mark.skipif(not rue_server_up(), reason="needs the RUE server (cd external/rue && npm run server)")


@needs_rue
def test_rue_social_round(tmp_path):
    work, social, phases = play_rue(tmp_path)
    assert {"work", "social actions"} <= phases
    assert social.rue.query(f"points(alice) = {work.scores()['alice']}")["count"] == 1
    assert "You like bob" in social.briefing("alice")
    # Every work event that happened became an occurrence, witnessed by its target.
    events = [e for line in (tmp_path / "events.jsonl").read_text().splitlines() for e in json.loads(line)["events"]]
    witnessed = social.rue.query("work_occurrence(?o) ^ witnessed(?o, ?w)")["rows"]
    assert len(witnessed) == len(events)
    # Each was registered as an external action of its kind. Its witnesses hold the actor
    # responsible in their own stores; the world doesn't, since the credit isn't public.
    takes = [e for e in events if e["kind"] == "took from"]
    assert social.rue.query('actionType(?o, "took from")')["count"] == len(takes)
    if takes:
        actor, target = takes[0]["actor"], takes[0]["target"]
        occ = social.rue.query(f'actionType(?o, "took from") ^ {target}.responsible(?o, {actor})')["rows"][0]["o"]
        assert social.rue.query(f"responsible({occ}, ?x)")["count"] == 0
        proof = json.dumps(social.rue.explain("witnessed", [occ, target]))
        assert "external, from work (round-" in proof and "chosen by" not in proof
        # What changed is recorded in the work's own quantity, attributed to the external action.
        assert social.rue.query(f'change({occ}, {target}, "points") = -2')["count"] == 1
        assert "external, from work (round-" in json.dumps(social.rue.explain("change", [occ, target, "points"]))


@needs_rue
def test_rue_event_with_no_credit_never_names_the_actor(tmp_path):
    _, social, _ = play_rue(tmp_path)
    event = WorkEvent(kind="hours lost to handoffs", actor="alice", witnesses=["alice", "bob", "carol", "dave"],
                      credit="none", changes={"bob": {"team hours lost": 3}}, text="The team lost 3 hours")
    occ = social.register(event)
    assert social.rue.query(f"witnessed({occ}, ?w)")["count"] == 4  # the actor too: it doesn't know it's credited
    assert social.rue.query(f"responsible({occ}, ?x)")["count"] == 0
    for agent in ("alice", "bob", "carol", "dave"):
        assert social.rue.query(f"{agent}.responsible({occ}, ?x)")["count"] == 0
    assert "alice" not in json.dumps(social.rue.explain("witnessed", [occ, "bob"]))


@needs_rue
def test_rue_left_alone_is_everyone_no_credited_event_touched_last_round(tmp_path):
    _, social, _ = play_rue(tmp_path)
    last = (tmp_path / "events.jsonl").read_text().splitlines()[-1]
    touched = {w for e in json.loads(last)["events"] if e["credit"] != "none" for w in e["witnesses"] if w != e["actor"]}
    alone = {a for a in AGENTS if social.rue.query(f"leftAlone({a})")["count"] == 1}
    assert alone == set(AGENTS) - touched


@needs_rue
def test_rue_menus_hide_the_ranking_and_apply_the_option_chosen(tmp_path):
    _, social, _ = play_rue(tmp_path)
    decisions = [json.loads(line) for line in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    social_decisions = [d for d in decisions if d["phase"] != "work"]
    assert social_decisions
    for d in social_decisions:
        options = d["request"]["options"]
        assert [o["id"] for o in options] == list(range(len(options)))  # ids are positions, not RUE's ranks
        assert d["request"]["show_scores"] is False
    # Each label an agent chose is the label RUE recorded, so the shuffled ids map back right.
    chosen = [next(o["label"] for o in d["request"]["options"] if o["id"] == d["decision"]["choice_id"])
              for d in social_decisions if d["phase"] == "work judgement"]
    for label in ("selfish", "careless", "fair", "generous", "bad luck"):
        count = sum(f"calls it {label}" in c for c in chosen)
        recorded = sum(social.rue.query(f'{a}.judgedAs(?o, "{label}")')["count"] for a in AGENTS)
        assert recorded == count, label


@needs_rue
def test_rue_menus_are_the_top_five_and_judgements_say_what_happened(tmp_path):
    _, social, _ = play_rue(tmp_path)
    decisions = [json.loads(line) for line in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    social_decisions = [d for d in decisions if d["phase"] != "work"]
    assert all(len(d["request"]["options"]) <= 5 for d in social_decisions)
    for d in social_decisions:
        briefing = d["request"]["briefing"]
        assert "The work:" not in briefing  # a social decision's Briefing is the social world alone
        if d["phase"] in ("work judgement", "social judgement"):
            assert "happened" in briefing and ": something." not in briefing
    # Each work judgement names the occurrence it's about, in the work event's own words.
    events = [e for line in (tmp_path / "events.jsonl").read_text().splitlines() for e in json.loads(line)["events"]]
    texts = {WorkEvent(**e).describe() for e in events}
    judged = [d for d in social_decisions if d["phase"] == "work judgement"]
    assert judged and all(any(t in d["request"]["briefing"] for t in texts) for d in judged)


def test_rue_menu_keeps_the_top_five_and_breaks_ties_at_random():
    social = RueSocial("social-layer-data", seed=1)
    scores = [9, 7, 3, 3, 3, 3, 3, 0, -2]
    kept = []
    for _ in range(30):
        menu = social.menu([{"index": i, "score": s} for i, s in enumerate(scores)])
        assert sorted((c["score"] for c in menu), reverse=True) == [9, 7, 3, 3, 3]
        kept.append(frozenset(c["index"] for c in menu if c["score"] == 3))
    assert len(set(kept)) > 1  # which of the tied 3s make the cut varies


def test_every_fact_a_priming_rule_reads_has_a_briefing_template():
    # A reason is a premise rendered with its predicate's `briefing` template; without
    # one it silently drops out of the agent's menu (ADR 0007).
    import re
    scenario = Path(__file__).parent.parent / "rue-data" / "social-layer-data"
    predicates = json.loads((scenario / "predicates.json").read_text())["predicates"]
    premises = []
    for rule in (scenario / "social-priming.rue").read_text().split('rule "')[1:]:
        lhs = rule.split("=>")[0]
        premises += re.findall(r"(?:\?[A-Z]+\.)?([A-Za-z][\w-]*)\(", lhs.split("\n", 1)[1])
    assert premises
    missing = sorted({p for p in premises if "briefing" not in predicates[p].get("toString", {})})
    assert not missing, f"no briefing template: {missing}"


@needs_rue
def test_rue_options_carry_reasons_without_ranking_numbers(tmp_path):
    play_rue(tmp_path)
    options = [o for line in (tmp_path / "decisions.jsonl").read_text().splitlines()
               for o in json.loads(line)["request"]["options"]]
    with_reasons = [o for o in options if o["reasons"]]
    assert with_reasons
    for o in with_reasons:
        for reason in o["reasons"]:
            assert reason["direction"] in ("for", "against") and "impulse" not in reason["text"]
