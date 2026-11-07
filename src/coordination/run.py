"""A Run: one complete play of some work with some social layer, under one Situation.

Each round:

1. Work moves: the work's decisions for this step go to their agents, each with its
   Briefing (the work, plus its social world). Work moves are unscored; the agent
   deliberates freely.
2. Resolve: the work applies the step's work moves at once and reports work events.
   Steps 1 and 2 repeat until the work's round has no decisions left (ADR 0005).
3. Mirror: the work state is copied into the social world as it is. Nothing is judged.
4. The social round, run by the social layer (for RUE, one tick of its tick plan):
   record the work events, work judgement, social actions, social judgement.

The work and the social layer are both swappable (Work, SocialLayer); the Run only
sequences them and builds every Decision Request.
"""

import json
from collections.abc import Callable
from pathlib import Path

from .agents import Chooser, Decision, DecisionLog, DecisionRequest, Option
from .situation import Situation
from .social import SocialLayer
from .work import Work


class Run:
    def __init__(self, work: Work, social: SocialLayer, choosers: dict[str, Chooser],
                 situation: Situation, run_dir: str | Path,
                 on_decision: Callable[[str, str, DecisionRequest, Decision], None] | None = None):
        self.work = work
        self.social = social
        self.choosers = choosers
        self.situation = situation
        self.on_decision = on_decision
        self.run_dir = Path(run_dir)
        self.log = DecisionLog(self.run_dir / "decisions.jsonl")
        self.round = 0

    def briefing(self, agent: str, phase: str, prompt: str) -> str:
        """A work move's Briefing is the work and the agent's social world; a social decision's
        is the social world alone, with the decision's own prompt (ADR 0007)."""
        parts = ["The work:", self.work.briefing(agent), ""] if phase == "work" else []
        social = self.social.briefing(agent)
        if social:
            parts += [social, ""]
        parts.append(prompt)
        return "\n".join(parts)

    def ask(self, agent: str, phase: str, prompt: str, options: list[Option]) -> Decision:
        """Put one decision to an agent and log it."""
        request = DecisionRequest(
            agent=agent,
            instructions=self.situation.instructions_for(agent),
            briefing=self.briefing(agent, phase, prompt),
            options=options,
            show_scores=False,  # agents choose freely: RUE's ranking is never shown
        )
        decision = self.choosers[agent].choose(request)
        self.log.write(request, decision, round=self.round, phase=phase)
        if self.on_decision:
            self.on_decision(agent, phase, request, decision)
        return decision

    def play(self) -> dict[str, float]:
        self.social.start(self.work.agents, self.situation.facts)
        while not self.work.over():
            self.round += 1
            self.work.next_round()
            events = []
            while pending := self.work.decisions():
                answers = {d.key: self.ask(d.agent, "work", d.prompt, d.options).choice_id for d in pending}
                events += self.work.resolve(answers)
            self._write("events.jsonl", {"round": self.round, "events": [e.model_dump() for e in events]})
            self.social.mirror(self.work.state())
            self.social.social_round(events, self.ask)
            self._write("rounds.jsonl", {
                "round": self.round,
                "scores": self.work.scores(),
                "work": self.work.record(),
                "social": {agent: self.social.briefing(agent) for agent in self.work.agents},
            })
        return self.work.scores()

    def _write(self, name: str, record: dict) -> None:
        with (self.run_dir / name).open("a") as f:
            f.write(json.dumps(record) + "\n")
