"""Choosers: anything that answers a DecisionRequest with a Decision.

The harness only depends on the Chooser protocol. LLM choosers are configured by
model profiles (models.toml); scripted and human choosers need no configuration.
"""

import logging
import os
from typing import Protocol

# Pydantic AI prints a promotional banner on first use unless this is set.
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
# Google's SDK warns about how Pydantic AI calls it, on every request.
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

from .decision import Decision, DecisionRequest, Option
from .llm import LLMChooser
from .log import DecisionLog
from .profiles import ModelProfile, load_profiles
from .scripted import HumanChooser, RandomChooser, TopRankedChooser


class Chooser(Protocol):
    kind: str

    def choose(self, request: DecisionRequest) -> Decision: ...


__all__ = [
    "Chooser", "Decision", "DecisionLog", "DecisionRequest", "HumanChooser", "LLMChooser",
    "ModelProfile", "Option", "RandomChooser", "TopRankedChooser", "load_profiles",
]
