"""The LLM chooser: asks a model, through Pydantic AI, to pick one option from a menu."""

import json
import time
from dataclasses import asdict
from typing import Literal

from pydantic import BaseModel, Field, create_model
from pydantic_ai import Agent, NativeOutput, PromptedOutput, ToolOutput
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ThinkingPart
from pydantic_ai.models import Model

from .decision import Decision, DecisionRequest
from .profiles import ModelProfile
from .prompt import render_instructions, render_prompt

OUTPUT_MODES = {"native": NativeOutput, "tool": ToolOutput, "prompted": PromptedOutput}


def choice_schema(request: DecisionRequest) -> type[BaseModel]:
    """The answer's schema for one menu. choice_id is restricted to the menu's ids, so a
    provider that enforces schemas cannot return an invalid choice. The rationale comes
    first, so the model states its reason before it commits to an id."""
    ids = tuple(option.id for option in request.options)
    return create_model(
        "Choice",
        rationale=(str, Field(description="One or two sentences on why you chose this option.")),
        choice_id=(Literal[ids], Field(description="The id of the option you choose.")),
    )


class LLMChooser:
    """Chooses through a model profile. A schema-invalid answer gets one retry; after that
    the agent passes, and the failure is recorded on the Decision."""

    kind = "agent"

    def __init__(self, profile: ModelProfile, model: Model | None = None):
        self.profile = profile
        self._agent = Agent(
            model or profile.build_model(),
            model_settings=profile.model_settings(),
            retries={"output": 1},
        )

    def choose(self, request: DecisionRequest) -> Decision:
        output_type = OUTPUT_MODES[self.profile.output_mode](choice_schema(request))
        start = time.perf_counter()
        try:
            result = self._agent.run_sync(
                render_prompt(request),
                instructions=render_instructions(request),
                output_type=output_type,
            )
        except UnexpectedModelBehavior as err:
            return self._decision(request, choice_id=None, error=str(err), start=start)

        messages = result.all_messages()
        reasoning = "\n".join(
            part.content for message in messages for part in message.parts if isinstance(part, ThinkingPart)
        )
        return self._decision(
            request,
            choice_id=result.output.choice_id,
            rationale=result.output.rationale,
            reasoning=reasoning or None,
            usage=asdict(result.usage),
            messages=json.loads(result.all_messages_json()),
            start=start,
        )

    def _decision(self, request: DecisionRequest, *, start: float, **fields) -> Decision:
        return Decision(
            chooser_kind=self.kind,
            chooser_id=request.agent,
            model=self.profile.name,
            latency_s=round(time.perf_counter() - start, 3),
            **fields,
        )
