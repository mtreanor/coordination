"""Choosers that aren't LLMs: fixed policies and a human at the keyboard."""

import random

from .decision import Decision, DecisionRequest


class TopRankedChooser:
    """Always takes the menu's default (top-ranked) option. The no-LLM baseline."""

    kind = "agent"

    def choose(self, request: DecisionRequest) -> Decision:
        default = next((o for o in request.options if o.is_default), None)
        best = default or max(request.options, key=lambda o: o.score or 0)
        return Decision(
            choice_id=best.id, rationale="took the top-ranked option",
            chooser_kind=self.kind, chooser_id=request.agent,
        )


class RandomChooser:
    """Picks uniformly at random, from a seeded generator."""

    kind = "agent"

    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)

    def choose(self, request: DecisionRequest) -> Decision:
        choice = self._rng.choice(request.options)
        return Decision(
            choice_id=choice.id, rationale="picked at random",
            chooser_kind=self.kind, chooser_id=request.agent,
        )


class HumanChooser:
    """Asks the person at the terminal."""

    kind = "player"

    def choose(self, request: DecisionRequest) -> Decision:
        ids = {o.id for o in request.options}
        while True:
            answer = input(f"  {request.agent}'s pick: ").strip()
            if answer.isdigit() and int(answer) in ids:
                note = input("  why? (optional): ").strip()
                return Decision(choice_id=int(answer), rationale=note or None, chooser_kind=self.kind)
            print("  not a valid id")
