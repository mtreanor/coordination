"""Run configs: a Run's settings as a TOML file in configs/ (ADR 0005).

The work's rules are code. A Run config chooses everything else:

    description = "..."
    work = "investment-club"          # a name in coordination.work.WORKS
    agents = ["ana", "bo", "cy"]      # optional: the work's default agents otherwise
    rounds = 3                        # optional: the work's own length otherwise (for short test Runs)
    situation = "neutral"             # a file in situations/, without .toml
    seed = 0

    [social]
    layer = "rue"                     # or "off" (the work-only condition)
    scenario = "social-layer-data"
    plan = "full"

    [choosers]
    default = "random"                # rue, random, ask, or a profile in models.toml
    bo = "claude-haiku"               # per-agent overrides
"""

import json
import subprocess
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .agents import Chooser, make_chooser
from .situation import Situation
from .social import NoSocial, RueSocial, SocialLayer
from .work import WORKS, Work


class SocialConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layer: str = "rue"
    scenario: str = "social-layer-data"
    plan: str = "full"
    server: str = "http://localhost:5174"


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "default"
    description: str = ""
    work: str = "stub"
    agents: list[str] | None = None
    rounds: int | None = None
    situation: str = "neutral"
    seed: int = 0
    social: SocialConfig = SocialConfig()
    choosers: dict[str, str] = {"default": "random"}

    @classmethod
    def load(cls, path: str | Path) -> "RunConfig":
        path = Path(path)
        if not path.exists():
            raise SystemExit(f"No Run config {path}")
        return cls(name=path.stem, **tomllib.loads(path.read_text()))

    def label(self) -> str:
        social = self.social.layer if self.social.layer == "off" else f"{self.social.layer}-{self.social.plan}"
        return f"{self.work}-{social}-{self.situation}"

    # Building the parts of a Run

    def make_work(self) -> Work:
        if self.work not in WORKS:
            raise SystemExit(f"No work {self.work!r} (known: {sorted(WORKS)})")
        return WORKS[self.work](self.agents, seed=self.seed, rounds=self.rounds)

    def make_social(self) -> SocialLayer:
        if self.social.layer == "off":
            return NoSocial()
        if self.social.layer == "rue":
            s = self.social
            return RueSocial(s.scenario, s.server, plan=s.plan, seed=self.seed)
        raise SystemExit(f"No social layer {self.social.layer!r} (known: off, rue)")

    def chooser_names(self, agents: list[str]) -> dict[str, str]:
        unknown = set(self.choosers) - set(agents) - {"default"}
        if unknown:
            raise SystemExit(f"Choosers for agents this Run doesn't have: {sorted(unknown)} (agents: {agents})")
        default = self.choosers.get("default", "random")
        return {agent: self.choosers.get(agent, default) for agent in agents}

    def make_choosers(self, agents: list[str]) -> dict[str, Chooser]:
        return {agent: make_chooser(name, self.seed + i)
                for i, (agent, name) in enumerate(self.chooser_names(agents).items())}

    def load_situation(self, agents: list[str], directory: str | Path = "situations") -> Situation:
        situation = Situation.load(self.situation, directory)
        unknown = set(situation.principals) - set(agents)
        if unknown:
            raise SystemExit(f"Situation {self.situation!r} has instructions for agents this Run "
                             f"doesn't have: {sorted(unknown)} (agents: {agents})")
        return situation

    def check_cast(self, agents: list[str], project_config: str | Path = "project.config.json") -> None:
        """With the RUE social layer, the Run's agents must be exactly the agents declared in
        the scenario's entities.json. RUE takes its agents only from that file, so the two are
        kept in sync by hand; this check fails before any decision is asked."""
        if self.social.layer != "rue":
            return
        declared, path = rue_agents(self.social.scenario, project_config)
        if set(declared) != set(agents):
            missing = sorted(set(agents) - set(declared))
            extra = sorted(set(declared) - set(agents))
            raise SystemExit(
                f"The Run's agents don't match RUE scenario {self.social.scenario!r} ({path}).\n"
                + (f"  Add to its \"agent\" entities: {missing}\n" if missing else "")
                + (f"  Drop from it, or add to the Run's agents: {extra}\n" if extra else "")
                + f"  Run agents: {agents}\n  Scenario agents: {declared}")

    def manifest(self, agents: list[str]) -> dict:
        """The resolved settings, for the Run directory's config.json."""
        return {**self.model_dump(), "agents": agents, "choosers": self.chooser_names(agents), "commit": _commit()}


ENTITY_TYPE_KEYS = {"privateStore", "distinct", "naming"}
"""Keys in an entities.json type that configure the type rather than name an instance."""


def rue_agents(scenario: str, project_config: str | Path = "project.config.json") -> tuple[list[str], Path]:
    """The agents a RUE scenario declares in its entities.json, read from disk, and that file."""
    project_config = Path(project_config)
    scenarios = json.loads(project_config.read_text()).get("scenarios", {})
    if scenario not in scenarios:
        raise SystemExit(f"No RUE scenario {scenario!r} in {project_config} (known: {sorted(scenarios)})")
    path = project_config.parent / scenarios[scenario] / "entities.json"
    agent_type = json.loads(path.read_text()).get("agent", {})
    return [name for name in agent_type if name not in ENTITY_TYPE_KEYS], path


def _commit() -> str | None:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None
