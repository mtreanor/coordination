"""The Work interface: what any version of the work provides to a Run.

The work is the only part of a Run that isn't RUE. It owns its own state, decides
which work moves are legal, resolves them, and reports what happened as work events.
It knows nothing about the social layer.
"""

from typing import Protocol

from pydantic import BaseModel

from ..agents import Option


class WorkFact(BaseModel):
    """One piece of work state, such as an agent's points, for the Mirror to copy into
    the social world as it is, with no judgement."""

    name: str
    args: list[str]
    value: float | bool = True


class WorkEvent(BaseModel):
    """Something that happened in the work that witnesses can judge (recorded in RUE as
    an occurrence)."""

    kind: str
    """What happened, e.g. "took_from". The social layer maps kinds to its own vocabulary."""
    actor: str
    target: str | None = None
    witnesses: list[str]
    """Every agent who saw it, the actor included."""


class Work(Protocol):
    name: str
    agents: list[str]

    def briefing(self, agent: str) -> str:
        """What this agent may know about the work right now: the rules, its own state,
        public state, and what it witnessed. Never hidden state (ADR 0003)."""
        ...

    def options(self, agent: str) -> list[Option]:
        """This agent's legal work moves this round. Unscored: the agent deliberates freely."""
        ...

    def state(self) -> list[WorkFact]:
        """The work state the social world mirrors, as ground truth. What each agent may
        know is still limited by its Briefing (ADR 0003)."""
        ...

    def resolve(self, choices: dict[str, int | None]) -> list[WorkEvent]:
        """Apply every agent's choice at once (None means the agent passed) and advance one
        round. Returns what happened."""
        ...

    def over(self) -> bool: ...

    def scores(self) -> dict[str, float]: ...
