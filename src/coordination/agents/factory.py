"""Building a chooser from its name on the command line."""

from .llm import LLMChooser
from .profiles import load_profiles
from .scripted import HumanChooser, RandomChooser, TopRankedChooser


def make_chooser(name: str, seed: int = 0):
    """rue (top-ranked), random (seeded), ask (a human at the terminal), or a model profile
    name from models.toml. A model gets `seed` as its sampling seed unless its profile sets
    one, so paired Runs (same Run seed) start each agent's model from the same seed, as far
    as the provider honours it (best effort for hosted models)."""
    if name == "rue":
        return TopRankedChooser()
    if name == "random":
        return RandomChooser(seed)
    if name == "ask":
        return HumanChooser()
    profiles = load_profiles()
    if name not in profiles:
        raise SystemExit(f"Unknown chooser {name!r}: use rue, random, ask, or one of {sorted(profiles)}")
    profile = profiles[name]
    if profile.seed is None:
        profile = profile.model_copy(update={"seed": seed})
    return LLMChooser(profile)
