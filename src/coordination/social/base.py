"""The SocialLayer interface: what any version of the social layer provides to a Run,
plus the version that switches it off.

The social layer holds the social world (dispositions, relationships, beliefs) and runs
everything social in a round. When it needs an agent to decide something (a judgement
action, a social action), it calls `ask`, and the Run builds the Decision Request: the
agent's standing instructions, the Briefing (the social world, without the work: ADR 0007), the
phase's prompt, and the menu the social layer supplies.
"""

from typing import Protocol

from ..agents import Decision, Option
from ..work import WorkEvent, WorkFact


class Ask(Protocol):
    def __call__(self, agent: str, phase: str, prompt: str, options: list[Option]) -> Decision: ...


class SocialLayer(Protocol):
    name: str
    introduction: str
    """The social world, described for the agents' standing instructions: what kinds of
    social decision there are, never which choice is worth making. Empty when off."""

    def start(self, agents: list[str], facts: list[str]) -> None:
        """Begin a Run with these agents and the Situation's starting facts."""
        ...

    def briefing(self, agent: str) -> str:
        """The agent's social world as text: everything it believes (empty when off)."""
        ...

    def mirror(self, state: list[WorkFact]) -> None:
        """Copy the work state into the social world as it is. Nothing is judged."""
        ...

    def social_round(self, events: list[WorkEvent], ask: Ask) -> None:
        """The social half of a round: record the work events, then whatever the social
        world's round runs (normally work judgement, social actions, social judgement)."""
        ...


MATCHED_INTRODUCTION = """\
Besides the work's rules, a few things hold throughout:
- each decision is put to you on its own, with what you know at that moment;
- what you know comes from the work's own record of what you did and what happened to you;
- you aren't told in advance how many rounds there will be.
Each time, you choose from a short list of set options, not a free-form answer.
Colleagues are named on each list in a shuffled order, so where someone appears says nothing about them.
The options you're offered come from the rules of the work: what each choice costs and what it does. They describe your situation; the choice is yours."""
"""The matched control's standing introduction (the prereg, docs/experiments/prereg-confirmatory.md):
about as long as RueSocial's and in the same register, true of every condition, with no social content, so a social
condition and the matched work-only condition differ in the social layer, not in the length or
tone of the system prompt (exp 7 found that difference could matter)."""


class NoSocial:
    """The social layer switched off: the work-only condition. `matched` gives it the matched
    control's introduction in place of none."""

    name = "off"
    introduction = ""

    def __init__(self, matched: bool = False):
        if matched:
            self.name = "off-matched"
            self.introduction = MATCHED_INTRODUCTION

    def start(self, agents: list[str], facts: list[str]) -> None: ...

    def briefing(self, agent: str) -> str:
        return ""

    def mirror(self, state: list[WorkFact]) -> None: ...

    def social_round(self, events: list[WorkEvent], ask: Ask) -> None: ...
