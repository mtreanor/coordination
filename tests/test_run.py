import os
import json
from pathlib import Path

import httpx
import pytest

from coordination.agents import DecisionRequest, RandomChooser
from coordination.config import RunConfig
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
        return "Your social world:\nAbout bob: You like them 7 out of 10."

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
    assert "The work:" in briefing and "Your social world:" in briefing
    assert len((tmp_path / "rounds.jsonl").read_text().splitlines()) == 2


def test_work_only_briefing_has_no_social_section(tmp_path):
    run = Run(StubWork(AGENTS), NoSocial(), {}, Situation(name="t"), tmp_path)
    assert "Your social world" not in run.briefing("alice", "work", "Choose.")


def test_situation_loads_special_instructions(tmp_path):
    (tmp_path / "s.toml").write_text('facts = ["x"]\n[special_instructions]\nbob = "Be selfish."\n')
    situation = Situation.load("s", tmp_path)
    assert situation.facts == ["x"]
    assert situation.instructions_for("bob") == "Be selfish."
    assert situation.instructions_for("alice") == ""  # no instructions beyond the work's own


def test_situations_combine_in_order(tmp_path):
    (tmp_path / "cast.toml").write_text('facts = ["a", "b"]\n')
    (tmp_path / "defector.toml").write_text('facts = ["c"]\n[special_instructions]\nbob = "Be selfish."\n')
    combined = RunConfig(situations=["cast", "defector"]).load_situation(AGENTS, tmp_path)
    assert combined.name == "cast+defector" and combined.facts == ["a", "b", "c"]
    assert combined.instructions_for("bob") == "Be selfish." and combined.instructions_for("alice") == ""
    neutral = RunConfig().load_situation(AGENTS, tmp_path)
    assert neutral.facts == [] and RunConfig().situation_label() == "neutral"


def test_no_agent_is_told_about_a_principal(tmp_path):
    from coordination.agents.prompt import render_instructions
    run = Run(StubWork(AGENTS), NoSocial(), {}, Situation(name="t"), tmp_path)
    text = render_instructions(DecisionRequest(agent="bob", setting=run.setting("bob"), options=[]))
    assert "principal" not in text.lower()
    # Every agent, every work: the incentive, stated without telling it what to aim for.
    assert "What you get out of this is your own score, and the work's rules say what it is." in text


RUE = os.environ.get("RUE_SERVER", "http://localhost:5174")
"""The RUE server the RUE tests use; it must be serving this project's current data
(scenario edits need a restart). RUE_SERVER=http://localhost:5240 for another one."""


def rue_server_up() -> bool:
    try:
        httpx.get(f"{RUE}/api/play/social-layer-data/session", timeout=1)
        return True
    except httpx.HTTPError:
        return False


def play_rue(tmp_path, **social_options):
    choosers = {agent: RandomChooser(i) for i, agent in enumerate(AGENTS)}
    work = StubWork(AGENTS, rounds=2)
    social = RueSocial("social-layer-data", server=RUE, **social_options)
    facts = Situation.load("office-history").facts + ["alice.likes(alice, bob) = 1"]
    run = Run(work, social, choosers, Situation(name="t", facts=facts), tmp_path)
    run.play()
    phases = {json.loads(line)["phase"] for line in (tmp_path / "decisions.jsonl").read_text().splitlines()}
    return work, social, phases


needs_rue = pytest.mark.skipif(not rue_server_up(), reason="needs the RUE server (cd external/rue && npm run server)")


@needs_rue
def test_rue_social_round(tmp_path):
    work, social, phases = play_rue(tmp_path)
    assert {"work", "social actions"} <= phases
    assert social.rue.query(f"points(alice) = {work.scores()['alice']}")["count"] == 1
    assert any(line.startswith("About bob: ") and "You like them" in line for line in social.briefing("alice").splitlines())
    # Every work event that happened became an occurrence, witnessed by its target in the
    # target's own store (only the two involved know), never in the shared world.
    events = [e for line in (tmp_path / "events.jsonl").read_text().splitlines() for e in json.loads(line)["events"]]
    witnessed = sum(social.rue.query(f"{a}.work_occurrence(?o) ^ {a}.witnessed(?o, {a})")["count"] for a in AGENTS)
    assert witnessed == len(events)
    assert social.rue.query("work_occurrence(?o)")["count"] == 0  # the shared world knows of none
    # Each was registered as an external action of its kind, known only to its witnesses: its
    # actionType and roles are in their stores, not the world's. Its witnesses hold the actor
    # responsible in their own stores; the world doesn't, since the credit isn't public.
    takes = [e for e in events if e["kind"] == "took from"]
    assert social.rue.query('actionType(?o, "took from")')["count"] == 0
    if takes:
        actor, target = takes[0]["actor"], takes[0]["target"]
        bystander = next(a for a in AGENTS if a not in (actor, target))
        occ = social.rue.query(f'{target}.actionType(?o, "took from") ^ {target}.responsible(?o, {actor})')["rows"][0]["o"]
        assert social.rue.query(f"responsible({occ}, ?x)")["count"] == 0
        for who in (actor, target):
            assert social.rue.query(f"{who}.role({occ}, ACTOR, {actor}) ^ {who}.role({occ}, TARGET, {target})")["count"] == 1
        assert social.rue.query(f"{bystander}.role({occ}, ?r, ?x)")["count"] == 0
        assert social.rue.query(f"role({occ}, ?r, ?x)")["count"] == 0
        proof = json.dumps(social.rue.explain("witnessed", [occ, target], owner=target))
        assert "external, from work (round-" in proof and "chosen by" not in proof
        # What changed is recorded in the work's own quantity, attributed to the external action,
        # in each witness's store.
        assert social.rue.query(f'{target}.change({occ}, {target}, "points") = -2')["count"] == 1
        assert social.rue.query(f'change({occ}, {target}, "points") = -2')["count"] == 0
        assert "external, from work (round-" in json.dumps(
            social.rue.explain("change", [occ, target, "points"], owner=target))


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
    social = RueSocial("social-layer-data", server=RUE, seed=1)
    scores = [9, 7, 3, 3, 3, 3, 3, 0, -2]
    kept = []
    for _ in range(30):
        menu = social.menu([{"index": i, "score": s} for i, s in enumerate(scores)])
        assert sorted((c["score"] for c in menu), reverse=True) == [9, 7, 3, 3, 3]
        kept.append(frozenset(c["index"] for c in menu if c["score"] == 3))
    assert len(set(kept)) > 1  # which of the tied 3s make the cut varies


def test_every_fact_a_priming_rule_reads_has_a_reason_template():
    # A reason is a premise rendered with its predicate's `reason` template; without one
    # it silently drops out of the agent's menu (ADR 0007).
    import re
    scenario = Path(__file__).parent.parent / "rue-data" / "social-layer-data"
    predicates = json.loads((scenario / "predicates.json").read_text())["predicates"]
    premises = []
    for rule in (scenario / "social-priming.rue").read_text().split('rule "')[1:]:
        lhs = rule.split("=>")[0]
        premises += re.findall(r"(?:\?[A-Z]+\.)?([A-Za-z][\w-]*)\(", lhs.split("\n", 1)[1])
    assert premises
    missing = sorted({p for p in premises if "reason" not in predicates[p].get("toString", {})})
    assert not missing, f"no reason template: {missing}"


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


@needs_rue
def test_rue_briefing_is_the_agents_social_state_by_colleague(tmp_path):
    _, social, _ = play_rue(tmp_path)
    briefing = social.briefing("carol")
    lines = briefing.splitlines()
    assert lines[0] == "Your social world:"
    assert lines[1].startswith("You: ") and "forgiving" in lines[1]  # carol's own traits
    about = [line.split(":")[0] for line in lines[2:]]
    assert about == sorted(about) and all(a.startswith("About ") for a in about)
    # Liking and grudges drift back toward neutral (social-drift.rue); friendship doesn't.
    assert any(line.startswith("About alice: ") and "friend" in line
               for line in social.briefing("dave").splitlines())
    assert "5 out of 10" not in briefing  # neutral values are left out
    # State, not history: no event the agent witnessed, and nothing from another's store.
    events = [WorkEvent(**e) for line in (tmp_path / "events.jsonl").read_text().splitlines()
              for e in json.loads(line)["events"]]
    assert not any(e.describe() in briefing for e in events)
    assert "know about" not in briefing and "verdict" not in briefing
    assert "rival" not in briefing  # bob's view of carol is bob's


def test_rue_reasons_shown_are_about_the_options_own_people():
    social = RueSocial("social-layer-data", server=RUE)
    social.agents = AGENTS
    social.occurrences = {"occ3": "bob passed their bug to dave", "occ1": "the team lost 2 hours"}
    reason = lambda *args: {"text": " ".join(args), "direction": "for", "fact": {"args": list(args)}}
    reasons = [reason("dave", "alice"), reason("dave", "bob"), reason("dave"), reason("occ3", "bob"),
               reason("occ1", "fair"), reason("occ1", "alice")]
    talking = {"binding": {"SELF": "dave", "OTHER": "alice"}, "reasons": reasons}
    assert [r["text"] for r in social.relevant(talking)] == ["dave alice", "dave", "occ1 alice"]
    judging = {"binding": {"SELF": "dave", "OCC": "occ3"}, "reasons": reasons}
    assert [r["text"] for r in social.relevant(judging)] == ["dave", "occ3 bob"]


@needs_rue
def test_rue_only_the_one_spoken_to_knows_what_was_said(tmp_path):
    # No overhearing, and the speaker doesn't see how it was taken (Mike, Nov 7).
    _, social, _ = play_rue(tmp_path)
    said = social._social_occurrences()
    assert said, "the grudge situation should make someone speak"
    assert social.rue.query("social_occurrence(?o)")["count"] == 0  # the shared world never learns
    for occ in said:
        assert social.rue.query(f"witnessed({occ}, ?w)")["count"] == 0  # not in the shared world
        assert social.rue.query(f"role({occ}, ?r, ?x)")["count"] == 0
        knowers = [a for a in AGENTS if social.rue.query(f"{a}.role({occ}, SELF, ?x)")["count"]]
        assert len(knowers) == 2  # the speaker and the one spoken to
        listeners = [a for a in AGENTS if social.rue.query(f"{a}.witnessed({occ}, {a})")["count"]]
        assert len(listeners) == 1
        for agent in AGENTS:
            assert social.occurrences[occ] not in social.briefing(agent)  # state, not history


@needs_rue
def test_rue_nobody_knows_of_a_work_event_they_did_not_witness(tmp_path):
    _, social, _ = play_rue(tmp_path)
    events = [WorkEvent(**e) for line in (tmp_path / "events.jsonl").read_text().splitlines()
              for e in json.loads(line)["events"]]
    partial = [e for e in events if set(e.witnesses) != set(AGENTS)]
    assert partial
    occurrences = {text: occ for occ, text in social.occurrences.items()}
    for event in partial:
        occ = occurrences[event.describe()]
        assert social.rue.query(f"witnessed({occ}, ?w)")["count"] == 0  # not shared
        for agent in AGENTS:
            knows = social.rue.query(f"{agent}.witnessed({occ}, {agent})")["count"] > 0
            assert knows == (agent in event.witnesses and (event.credit == "none" or agent != event.actor))
    # An event every agent witnessed is shared, in the world.
    public = WorkEvent(kind="hours lost to handoffs", witnesses=AGENTS, credit="none",
                       changes={}, text="The team lost 2 hours to handoffs")
    occ = social.register(public)
    assert social.rue.query(f"witnessed({occ}, ?w)")["count"] == len(AGENTS)


def test_system_prompt_is_overview_work_and_social_world(tmp_path):
    from coordination.agents.prompt import render_instructions
    from coordination.social.rue import INTRODUCTION as SOCIAL_INTRODUCTION
    from coordination.work.stub import INTRODUCTION as WORK_INTRODUCTION

    class Social(NoSocial):
        introduction = SOCIAL_INTRODUCTION

    situation = Situation(name="t", special_instructions={"bob": "Get points."})
    setting = Run(StubWork(AGENTS), Social(), {}, situation, tmp_path).setting("alice")
    assert setting.startswith("You are alice. You work with ")
    first_line = setting.splitlines()[0]
    assert all(name in first_line for name in ("bob", "carol", "dave"))  # in a seeded random order
    assert setting.index(WORK_INTRODUCTION) < setting.index(SOCIAL_INTRODUCTION)
    for word in ("complain", "praise", "confront", "selfish", "generous"):
        assert word not in setting.lower()  # the social world is described in the abstract
    # The work-only condition describes no social world.
    assert "social life" not in Run(StubWork(AGENTS), NoSocial(), {}, situation, tmp_path).setting("alice")
    # Special instructions come last, after the standing introduction.
    run = Run(StubWork(AGENTS), Social(), {}, situation, tmp_path)
    request = DecisionRequest(agent="bob", setting=run.setting("bob"), instructions="Get points.", options=[])
    text = render_instructions(request)
    assert text.startswith("You are bob.") and text.endswith("Special instructions:\nGet points.")


def test_matched_control_has_a_neutral_introduction_of_similar_length(tmp_path):
    from coordination.social import MATCHED_INTRODUCTION
    from coordination.social.rue import INTRODUCTION as SOCIAL_INTRODUCTION

    setting = Run(StubWork(AGENTS), NoSocial(matched=True), {}, Situation(name="t"), tmp_path).setting("alice")
    assert setting.endswith(MATCHED_INTRODUCTION)
    for word in ("social", "colleague said", "feel", "trust", "like"):
        assert word not in MATCHED_INTRODUCTION.lower()
    assert 0.85 < len(MATCHED_INTRODUCTION.split()) / len(SOCIAL_INTRODUCTION.split()) < 1.15


@needs_rue
def test_feelings_drift_toward_neutral_without_fresh_dealings():
    from coordination.rue_client import RueClient
    rue = RueClient("social-layer-data", RUE)
    rue.reset()
    rue.start(controlled_agents=[])
    for fact in Situation.load("office-history").facts:
        rue.assert_fact(fact)
    rue.set_plan([{"ruleset": "social-drift", "mode": "single"}])  # nothing happens, so nothing is fresh
    rue.step()
    assert rue.query("dave.trusts(dave, carol) = 5")["count"] == 1      # was 4
    assert rue.query("dave.likes(dave, bob) = 5")["count"] == 1         # was 6, and bob isn't a friend
    assert rue.query("dave.likes(dave, alice) = 7")["count"] == 1       # a friend: doesn't fade
    assert rue.query("carol.grudge(carol, bob) = 1")["count"] == 1      # was 3; carol is forgiving
    rue.reset()


@needs_rue
def test_saying_the_same_thing_again_counts_against_it(tmp_path):
    play_rue(tmp_path)
    reasons = [r for line in (tmp_path / "decisions.jsonl").read_text().splitlines()
               for o in json.loads(line)["request"]["options"] for r in o["reasons"]
               if r["text"].startswith("You've told ") or r["text"].endswith(" recently.")]
    assert all(r["direction"] == "against" for r in reasons)


@needs_rue
def test_strong_feelings_settle_and_grudges_fade_without_a_grievance():
    # Mending (exp/3-reform): with no grievance, a grudge fades; strong feelings settle
    # every round, whatever happens.
    from coordination.rue_client import RueClient
    rue = RueClient("social-layer-data", RUE)
    rue.reset()
    rue.start(controlled_agents=[])
    for fact in ["alice.likes(alice, bob) = 10", "alice.grudge(alice, carol) = 3", "alice.grateful(alice, dave) = 8"]:
        rue.assert_fact(fact)
    rue.set_plan([{"ruleset": "social-drift", "mode": "single"}])
    rue.step()
    assert rue.query("alice.likes(alice, bob) = 8")["count"] == 1        # fades and settles
    assert rue.query("alice.grudge(alice, carol) = 2")["count"] == 1     # fades
    assert rue.query("alice.grateful(alice, dave) = 6")["count"] == 1    # fades and settles
    rue.reset()
