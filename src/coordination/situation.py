"""Situations: the authored starting conditions of a Run (see CONTEXT.md).

A Situation is a TOML file in situations/:

    description = "..."
    instructions = "Instructions every agent is given."   # optional
    facts = ["alice.likes(alice, bob) = 1"]   # asserted into RUE at the start

    [special_instructions]
    bob = "Instructions for bob only."

Facts are RUE statements, so they apply only when the social layer is RUE.

A Run can combine several Situations, in order (`Situation.combine`): one for the
cast's starting relationships, say, and another that gives one agent special
instructions. No Situations at all is the neutral start: every relationship at its
default and no instructions beyond the work's own.
"""

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Situation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    instructions: str = ""
    special_instructions: dict[str, str] = {}
    facts: list[str] = []

    def instructions_for(self, agent: str) -> str:
        """What the agent is told beyond the work's own introduction: the instructions every
        agent is given, then its own special instructions. Empty when there are none."""
        return "\n".join(text for text in (self.instructions, self.special_instructions.get(agent, "")) if text)

    @classmethod
    def load(cls, name: str, directory: str | Path = "situations") -> "Situation":
        path = Path(directory) / f"{name}.toml"
        if not path.exists():
            known = sorted(p.stem for p in Path(directory).glob("*.toml"))
            raise SystemExit(f"No situation {name!r} in {directory}/ (known: {known})")
        return cls(name=name, **tomllib.loads(path.read_text()))

    @classmethod
    def combine(cls, situations: list["Situation"]) -> "Situation":
        """Several Situations as one, in order: facts and instructions add up, and an agent's
        special instructions from each are joined. No Situations is the neutral start."""
        if not situations:
            return cls(name="neutral", description="A neutral start: no relationships, no instructions.")
        if len(situations) == 1:
            return situations[0]
        special: dict[str, list[str]] = {}
        for s in situations:
            for agent, text in s.special_instructions.items():
                special.setdefault(agent, []).append(text)
        return cls(
            name="+".join(s.name for s in situations),
            description=" ".join(s.description for s in situations if s.description),
            instructions="\n".join(s.instructions for s in situations if s.instructions),
            special_instructions={agent: "\n".join(texts) for agent, texts in special.items()},
            facts=[fact for s in situations for fact in s.facts],
        )
