"""Model profiles: named, validated model configurations loaded from models.toml."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic_ai.models import Model, infer_model
from pydantic_ai.settings import ModelSettings

OLLAMA_DEFAULT_URL = "http://localhost:11434/v1"

ThinkingSetting = bool | Literal["minimal", "low", "medium", "high", "xhigh"]

# How each thinking setting maps onto Ollama's reasoning_effort (None: the model's default).
OLLAMA_REASONING_EFFORT = {
    False: "none", True: None, "minimal": "low", "low": "low",
    "medium": "medium", "high": "high", "xhigh": "high",
}


class ModelProfile(BaseModel):
    """One named model configuration. Unknown keys are rejected, so typos fail at load."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    provider: str
    """A Pydantic AI provider name: "ollama", "anthropic", "openai", "google", ..."""
    model: str
    """The provider's own model id."""
    base_url: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    thinking: ThinkingSetting = False
    """Off by default; True or an effort level turns the model's reasoning on."""
    output_mode: Literal["native", "tool", "prompted"] = "native"
    """How the answer's schema is sent: native JSON-schema output, a forced tool call, or prompting."""

    def build_model(self) -> Model:
        if self.provider == "ollama":
            from pydantic_ai.models.ollama import OllamaModel
            from pydantic_ai.providers.ollama import OllamaProvider

            return OllamaModel(self.model, provider=OllamaProvider(base_url=self.base_url or OLLAMA_DEFAULT_URL))
        return infer_model(f"{self.provider}:{self.model}")

    def model_settings(self) -> ModelSettings:
        settings: ModelSettings = {"thinking": self.thinking}
        if self.provider == "ollama":
            # Pydantic AI's unified `thinking` setting doesn't reach Ollama, so a
            # thinking model like Qwen 3.5 reasons anyway. Ollama's OpenAI-compatible
            # endpoint takes reasoning_effort instead, with "none" switching it off.
            effort = OLLAMA_REASONING_EFFORT[self.thinking]
            if effort is not None:
                settings["extra_body"] = {"reasoning_effort": effort}
        if self.temperature is not None:
            settings["temperature"] = self.temperature
        if self.max_tokens is not None:
            settings["max_tokens"] = self.max_tokens
        if self.seed is not None:
            settings["seed"] = self.seed
        return settings


def load_profiles(path: str | Path = "models.toml") -> dict[str, ModelProfile]:
    """Read every [profiles.<name>] table from a TOML file."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return {name: ModelProfile(name=name, **table) for name, table in data.get("profiles", {}).items()}
