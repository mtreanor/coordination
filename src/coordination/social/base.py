"""The SocialLayer interface: what any version of the social layer provides to a Run,
plus the version that switches it off.

The social layer holds the social world (dispositions, relationships, beliefs) and runs
everything social in a round. When it needs an agent to decide something (a judgement
action, a social action), it calls `ask`, and the Run builds the Decision Request: the
principal's instructions, the full Briefing (work and social world), the phase's prompt,
and the menu the social layer supplies.
"""

from typing import Protocol

from ..agents import Decision, Option
from ..work import WorkEvent, WorkFact


class Ask(Protocol):
    def __call__(self, agent: str, phase: str, prompt: str, options: list[Option]) -> Decision: ...


class SocialLayer(Protocol):
    name: str

    def start(self, agents: list[str], facts: list[str]) -> None:
        """Begin a Run with these agents and the Situation's starting facts."""
        ...

    def briefing(self, agent: str) -> str:
        """The agent's social world as text: everything it believes (empty when off)."""
        ...

    def mirror(self, state: list[WorkFact]) -> None:
        """Copy the work state into the social world as it is. Nothing is judged."""
        ...

    def record(self, events: list[WorkEvent]) -> None:
        """Record the work events so their witnesses can judge them."""
        ...

    def work_judgement(self, ask: Ask) -> None:
        """Witnesses judge the work events just recorded."""
        ...

    def social_actions(self, ask: Ask) -> None:
        """Agents take social actions between work moves."""
        ...

    def social_judgement(self, ask: Ask) -> None:
        """Listeners judge the social actions just taken."""
        ...


class NoSocial:
    """The social layer switched off: the work-only condition."""

    name = "off"

    def start(self, agents: list[str], facts: list[str]) -> None: ...

    def briefing(self, agent: str) -> str:
        return ""

    def mirror(self, state: list[WorkFact]) -> None: ...

    def record(self, events: list[WorkEvent]) -> None: ...

    def work_judgement(self, ask: Ask) -> None: ...

    def social_actions(self, ask: Ask) -> None: ...

    def social_judgement(self, ask: Ask) -> None: ...
