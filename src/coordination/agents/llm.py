"""The LLM chooser: asks a model, through Pydantic AI, to pick one option from a menu."""

import json
import random
import re
import time
from dataclasses import asdict
from typing import Literal

from pydantic import BaseModel, Field, create_model
from pydantic_ai import Agent, NativeOutput, PromptedOutput, ToolOutput
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ThinkingPart
from pydantic_ai.models import Model

from .decision import Decision, DecisionRequest
from .profiles import ModelProfile
from .prompt import render_instructions, render_prompt

OUTPUT_MODES = {"native": NativeOutput, "tool": ToolOutput, "prompted": PromptedOutput}

# Provider errors worth waiting out: timeouts, rate limits, and overloads.
TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
MAX_WAIT_S = 300
"""The longest wait a provider may ask for before the Run stops instead of waiting."""


def requested_delay(err: ModelHTTPError) -> float | None:
    """How long the provider asked us to wait, if it said: a Retry-After header, or
    Google's RetryInfo retryDelay (e.g. "22s") in the error body."""
    retry_after = (err.headers or {}).get("retry-after")
    if retry_after and retry_after.replace(".", "", 1).isdigit():
        return float(retry_after)
    match = re.search(r"'retryDelay': '([\d.]+)s'", str(err.body))
    return float(match.group(1)) if match else None


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


def usage_dict(usage) -> dict:
    """Token counts and cost as plain JSON values. Hosted providers report cost as a
    Decimal (in dollars); local models report none."""
    fields = asdict(usage)
    if fields.get("cost") is not None:
        fields["cost"] = float(fields["cost"])
    return fields


class LLMChooser:
    """Chooses through a model profile. A schema-invalid answer gets one retry; after that
    the agent passes, and the failure is recorded on the Decision.

    A transient provider error (rate limit, overload) is retried with exponential backoff.
    If it persists, the error is raised: an outage is not agent behavior, so it must stop
    the Run rather than turn into passes in the data."""

    kind = "agent"

    def __init__(self, profile: ModelProfile, model: Model | None = None,
                 api_attempts: int = 8, backoff_s: float = 2.0):
        self.profile = profile
        self.api_attempts = api_attempts
        self.backoff_s = backoff_s
        self._agent = Agent(
            model or profile.build_model(),
            model_settings=profile.model_settings(),
            retries={"output": 1},
        )

    def choose(self, request: DecisionRequest) -> Decision:
        output_type = OUTPUT_MODES[self.profile.output_mode](choice_schema(request))
        start = time.perf_counter()
        try:
            result = self._run_with_backoff(request, output_type)
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
            usage=usage_dict(result.usage),
            messages=json.loads(result.all_messages_json()),
            start=start,
        )

    def _run_with_backoff(self, request: DecisionRequest, output_type):
        for attempt in range(1, self.api_attempts + 1):
            try:
                return self._agent.run_sync(
                    render_prompt(request),
                    instructions=render_instructions(request),
                    output_type=output_type,
                )
            except ModelHTTPError as err:
                if err.status_code not in TRANSIENT_STATUS or attempt == self.api_attempts:
                    raise
                backoff = min(self.backoff_s * 2 ** (attempt - 1), 60) * random.uniform(0.8, 1.2)
                requested = requested_delay(err) or 0
                if requested > MAX_WAIT_S:
                    # A quota, not a blip (Google asks for ~12 hours when the daily quota
                    # is used up): stop the Run now rather than sleep through it.
                    raise RuntimeError(f"{self.profile.name}: HTTP {err.status_code}, provider asks to wait "
                                       f"{requested:.0f}s (quota exhausted?)") from err
                delay = max(backoff, requested)
                print(f"  ({self.profile.name}: HTTP {err.status_code}, retrying in {delay:.0f}s)")
                time.sleep(delay)

    def _decision(self, request: DecisionRequest, *, start: float, **fields) -> Decision:
        return Decision(
            chooser_kind=self.kind,
            chooser_id=request.agent,
            model=self.profile.name,
            latency_s=round(time.perf_counter() - start, 3),
            **fields,
        )
