import json

from coordination.agents import RandomChooser
from coordination.run import Run
from coordination.situation import Situation
from coordination.social import NoSocial
from coordination.work import NotMyBugWork

AGENTS = ["ana", "bo", "cy", "dee", "eli"]


def play(work, moves):
    """moves: agent -> label (missing agents pass)."""
    work.next_round()
    decisions = {d.agent: d for d in work.decisions()}
    answers = {a: next(o.id for o in decisions[a].options if o.label.startswith(label + " (")) for a, label in moves.items()}
    return work.resolve(answers)


def test_passing_wastes_an_hour_and_helping_moves_one():
    work = NotMyBugWork(AGENTS)
    events = play(work, {
        "ana": "Pass your bug to bo",
        "bo": "Fix your bug yourself",
        "cy": "Fix your bug yourself and help bo",
        "dee": "Fix your bug yourself",
        "eli": "Fix your bug yourself",
    })
    # ana passes for free; bo fixes his own (1) plus ana's (2), less cy's help (1); cy pays 2.
    assert work.scores() == {"ana": 10, "bo": 8, "cy": 8, "dee": 9, "eli": 9}
    assert sum(work.scores().values()) == 45 - 1  # one pass loses exactly one hour
    assert [(e.kind, e.actor, e.credit, e.changes) for e in events] == [
        ("passed a bug to", "ana", "witnesses", {"ana": {"hours": 1}, "bo": {"hours": -2}}),  # ana's hour saved
        ("helped with a bug", "cy", "witnesses", {"cy": {"hours": -1}, "bo": {"hours": 1}}),
        ("hours lost to handoffs", None, "none", {}),
    ]
    assert events[-1].shared_changes == {"velocity (hours shipped)": -1}
    assert "ana" not in events[2].describe()  # everyone sees the loss, nobody sees who passed
    assert all(set(e.witnesses) == {e.actor, e.target} for e in events[:2]) and events[2].witnesses == AGENTS
    bo = work.briefing("bo")
    assert "ana passed their bug to you. It cost you 2 hours." in bo and "cy helped you. It spared you 1 hour." in bo
    assert "44 hours shipped of a possible 45; 1 lost to handoffs; 1 went to helping colleagues" in work.briefing("dee")
    assert "ana" not in work.briefing("dee").split("Your past sprints:")[1].split("velocity")[0]  # dee saw nothing
    assert work.decisions() == []


def test_help_for_someone_with_nothing_to_fix_comes_back():
    work = NotMyBugWork(AGENTS)
    play(work, {"ana": "Pass your bug to cy", "bo": "Fix your bug yourself and help ana",
                "cy": "Fix your bug yourself", "dee": "Fix your bug yourself", "eli": "Fix your bug yourself"})
    assert work.scores()["bo"] == 9  # bo got the hour back
    assert "ana had nothing left to fix" in work.briefing("bo")
    assert work.record()["unneeded_help"] == ["bo"]


def test_a_pass_on_the_work_decision_fixes_your_own_bug():
    work = NotMyBugWork(AGENTS, rounds=1)
    play(work, {})
    assert work.scores() == {a: 9 for a in AGENTS}
    assert work.over()


def test_menus_are_shuffled_by_the_seed():
    def firsts(seed):
        work = NotMyBugWork(AGENTS, seed=seed)
        out = []
        for _ in range(3):
            work.next_round()
            out += [d.options[1].label for d in work.decisions()]
            work.resolve({})
        return out
    assert firsts(3) == firsts(3) and len(set(firsts(3))) > 3


def test_a_full_run(tmp_path):
    work = NotMyBugWork(AGENTS, rounds=3)
    choosers = {a: RandomChooser(i) for i, a in enumerate(AGENTS)}
    Run(work, NoSocial(), choosers, Situation(name="t"), tmp_path).play()
    rounds = [json.loads(line) for line in (tmp_path / "rounds.jsonl").read_text().splitlines()]
    assert [r["work"]["round"] for r in rounds] == [1, 2, 3]
    last = rounds[-1]["work"]
    assert sum(last["shipped"].values()) == 45 - last["lost_to_handoffs"]
