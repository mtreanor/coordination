import json

import httpx
import pytest

from coordination.agents import RandomChooser
from coordination.run import Run
from coordination.situation import Situation
from coordination.social import NoSocial, RueSocial
from coordination.work import StubWork

AGENTS = ["alice", "bob", "carol", "dave"]


def test_stub_work_moves_and_witnesses():
    work = StubWork(AGENTS, rounds=1)
    menus = {agent: work.options(agent) for agent in AGENTS}
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
    assert "alice took 2 points from you." in work.briefing("bob")
    assert "alice" not in work.briefing("dave").split("In the last round:")[1]
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
    assert "What you believe" not in run.briefing("alice", "Choose.")


def test_situation_loads_principal_instructions(tmp_path):
    (tmp_path / "s.toml").write_text('facts = ["x"]\n[principals]\nbob = "Be selfish."\n')
    situation = Situation.load("s", tmp_path)
    assert situation.facts == ["x"]
    assert situation.instructions_for("bob") == "Be selfish."
    assert situation.instructions_for("alice") == situation.instructions


def rue_server_up() -> bool:
    try:
        httpx.get("http://localhost:5174/api/play/stub-social/session", timeout=1)
        return True
    except httpx.HTTPError:
        return False


def play_rue(tmp_path, **social_options):
    choosers = {agent: RandomChooser(i) for i, agent in enumerate(AGENTS)}
    work = StubWork(AGENTS, rounds=2)
    social = RueSocial("stub-social", **social_options)
    run = Run(work, social, choosers, Situation(name="t", facts=["alice.likes(alice, bob) = 1"]), tmp_path)
    run.play()
    phases = {json.loads(line)["phase"] for line in (tmp_path / "decisions.jsonl").read_text().splitlines()}
    return work, social, phases


needs_rue = pytest.mark.skipif(not rue_server_up(), reason="needs the RUE server (cd external/rue && npm run server)")


@needs_rue
def test_rue_no_judgement_plan_skips_judgement(tmp_path):
    _, _, phases = play_rue(tmp_path, plan="no-judgement")
    assert phases == {"work", "social actions"}


@needs_rue
def test_rue_judgement_by_ranking_never_asks(tmp_path):
    _, social, phases = play_rue(tmp_path, rue_judgement=True)
    assert "work judgement" not in phases and "social judgement" not in phases
    assert social.rue.query("judged(?j, ?o)")["count"] > 0


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
    # Each was registered as an external action of its kind, with its actor as the SELF role.
    takes = [e for e in events if e["kind"] == "took from"]
    assert social.rue.query('actionType(?o, "took from")')["count"] == len(takes)
    if takes:
        occ = social.rue.query(f'actionType(?o, "took from") ^ role(?o, SELF, {takes[0]["actor"]})')["rows"][0]["o"]
        target = takes[0]["target"]
        proof = json.dumps(social.rue.explain("witnessed", [occ, target]))
        assert "external, from work (round-" in proof and "chosen by" not in proof
