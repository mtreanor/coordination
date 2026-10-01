"""The data that crosses the Chooser boundary: what an agent is asked, and what it answers."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Option(BaseModel):
    """One entry on a decision's menu."""

    id: int
    label: str
    score: float | None = None
    """The option's utility as ranked by the system that built the menu, if any."""
    is_default: bool = False
    """Whether this is the option the menu's own policy would pick unaided."""


class DecisionRequest(BaseModel):
    """Everything an agent is shown for one decision (see CONTEXT.md: Decision Request)."""

    agent: str
    instructions: str = ""
    """The principal's instructions to its agent."""
    briefing: str = ""
    """The situation the agent is shown, already rendered as text."""
    options: list[Option]
    show_scores: bool = True
    """Whether the menu shows each option's score to the agent as guidance."""


class Decision(BaseModel):
    """A chooser's answer to a DecisionRequest."""

    choice_id: int | None
    """The chosen option's id, or None to pass (no option is taken)."""
    rationale: str | None = None
    chooser_kind: Literal["agent", "player"]
    chooser_id: str | None = None
    reasoning: str | None = None
    """The model's hidden reasoning, when thinking was enabled."""
    model: str | None = None
    """The model profile that answered, for LLM choosers."""
    error: str | None = None
    """Why the chooser passed, when it passed because it failed."""
    latency_s: float | None = None
    usage: dict[str, Any] | None = None
    messages: list[Any] | None = Field(default=None, repr=False)
    """The full model exchange, for the decision log."""

    @property
    def passed(self) -> bool:
        return self.choice_id is None

    def rue_chooser(self) -> dict[str, str]:
        """The chooser object RUE records on the chosen action's ActionRecord."""
        chooser = {"kind": self.chooser_kind}
        if self.chooser_id is not None:
            chooser["id"] = self.chooser_id
        if self.rationale:
            chooser["note"] = self.rationale
        return chooser
