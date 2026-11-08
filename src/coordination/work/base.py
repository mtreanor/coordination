"""The Work interface: what any version of the work provides to a Run (ADR 0004, 0005, 0006).

The work is the only part of a Run that isn't RUE. It owns its own state, decides
which work moves are legal, resolves them, and reports what happened as work events.
It knows nothing about the social layer.

A round can have several steps (invest, then pay back). Each step is a set of
simultaneous work decisions; the Run asks them, then resolves the step.
"""

from typing import Literal, Protocol

from pydantic import BaseModel, model_validator

from ..agents import Option


class WorkFact(BaseModel):
    """One piece of work state, such as an agent's points, for the Mirror to copy into
    the social world as it is, with no judgement."""

    name: str
    args: list[str]
    value: float | bool = True


class WorkEvent(BaseModel):
    """Something that happened in the work that agents can judge (recorded in RUE as an
    occurrence, ADR 0006).

    An event reports what changed, in the work's own quantities, and who is credited with
    it, as far as anyone can see. Nothing more: whether a change was good or bad for an agent,
    and by how much, depends on that agent's strategy, so the social world never decides it
    (interfere as little as possible with the agents' strategies)."""

    kind: str
    """What happened, in the work's own words, e.g. "invested in". A label for people;
    no rule matches on it."""
    actor: str | None = None
    """Who actually did it: ground truth for the log. RUE learns it only through `credit`."""
    target: str | None = None
    witnesses: list[str]
    """Every agent who knows it happened, the actor included."""
    credit: Literal["witnesses", "public", "none"] = "witnesses"
    """Who knows the actor did it: its witnesses, everyone, or nobody. With "none", the
    witnesses know only what happened, and may hold someone responsible themselves."""
    changes: dict[str, dict[str, float]] = {}
    """What changed for each agent, by quantity, in the work's own terms: what literally
    happened, e.g. {"carol": {"hours": -2}}. Every agent named must be a witness."""
    shared_changes: dict[str, float] = {}
    """What changed for the group as a whole, by quantity, e.g. {"velocity (hours shipped)": -1}:
    a group-wide quantity rather than any one agent's. Known to the witnesses."""
    details: dict[str, float] = {}
    """The work's own numbers (amount, stake), for the log. The social world never reads them."""
    text: str | None = None
    """How the witnesses would describe it, e.g. "ana invested 10 coins in bo". With no
    credit it must not name the actor."""

    @model_validator(mode="after")
    def _check(self) -> "WorkEvent":
        unaware = set(self.changes) - set(self.witnesses)
        if unaware:
            raise ValueError(f"changes names {sorted(unaware)}, who aren't witnesses")
        if self.credit != "none" and self.actor is None:
            raise ValueError("an event credited to someone needs an actor")
        if self.credit == "none" and self.text is None:
            raise ValueError("an event with no credit needs text that doesn't name the actor")
        return self

    def describe(self) -> str:
        return self.text or " ".join(p for p in (self.actor, self.kind, self.target) if p)


class WorkDecision(BaseModel):
    """One question for one agent in the current step of a round."""

    key: str
    """Unique within the step, e.g. "invest:ana" or "payback:bo:ana". Answers come back by key."""
    agent: str
    prompt: str
    options: list[Option]


class Work(Protocol):
    """A work is constructed as Work(agents, seed=..., rounds=None): its rules are code,
    and rounds=None means the work's own length."""

    name: str
    agents: list[str]
    introduction: str
    """The work, set out for the agents' standing instructions: the scene, not the rules
    (those are in the Briefing each turn)."""

    def next_round(self) -> None:
        """Start the next round."""
        ...

    def decisions(self) -> list[WorkDecision]:
        """The decisions due now, all simultaneous. Empty means the round is done."""
        ...

    def resolve(self, answers: dict[str, int | None]) -> list[WorkEvent]:
        """Apply every answer to the current step at once (by decision key; None means
        the agent passed). Returns what happened."""
        ...

    def briefing(self, agent: str) -> str:
        """What this agent may know about the work right now: the rules, its own state,
        public state, and what it witnessed. Never hidden state (ADR 0003)."""
        ...

    def state(self) -> list[WorkFact]:
        """The work state the social world mirrors, as ground truth. What each agent may
        know is still limited by its Briefing (ADR 0003)."""
        ...

    def record(self) -> dict:
        """Ground truth for the Run's log only (e.g. hidden dice). Never mirrored into RUE."""
        ...

    def over(self) -> bool:
        """Checked between rounds."""
        ...

    def scores(self) -> dict[str, float]: ...
