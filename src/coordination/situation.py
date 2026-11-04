"""Situations: the authored starting conditions of a Run (see CONTEXT.md).

A Situation is a TOML file in situations/:

    description = "..."
    instructions = "What every principal tells its agent."
    facts = ["alice.likes(alice, bob) = 1"]   # asserted into RUE at the start

    [principals]
    bob = "Instructions for bob's principal only."

Facts are RUE statements, so they apply only when the social layer is RUE.
"""

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

DEFAULT_INSTRUCTIONS = "Your principal is scored only on how well you do in the work."


class Situation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    instructions: str = DEFAULT_INSTRUCTIONS
    principals: dict[str, str] = {}
    facts: list[str] = []

    def instructions_for(self, agent: str) -> str:
        return self.principals.get(agent, self.instructions)

    @classmethod
    def load(cls, name: str, directory: str | Path = "situations") -> "Situation":
        path = Path(directory) / f"{name}.toml"
        if not path.exists():
            known = sorted(p.stem for p in Path(directory).glob("*.toml"))
            raise SystemExit(f"No situation {name!r} in {directory}/ (known: {known})")
        return cls(name=name, **tomllib.loads(path.read_text()))
