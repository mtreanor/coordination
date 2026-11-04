"""Building a chooser from its name on the command line."""

from .llm import LLMChooser
from .profiles import load_profiles
from .scripted import HumanChooser, RandomChooser, TopRankedChooser


def make_chooser(name: str, seed: int = 0):
    """rue (top-ranked), random (seeded), ask (a human at the terminal), or a model profile
    name from models.toml."""
    if name == "rue":
        return TopRankedChooser()
    if name == "random":
        return RandomChooser(seed)
    if name == "ask":
        return HumanChooser()
    profiles = load_profiles()
    if name not in profiles:
        raise SystemExit(f"Unknown chooser {name!r}: use rue, random, ask, or one of {sorted(profiles)}")
    return LLMChooser(profiles[name])
