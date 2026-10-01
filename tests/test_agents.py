import json

import pytest
from pydantic_ai.messages import ModelResponse, RetryPromptPart, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from coordination.agents import (
    DecisionRequest, LLMChooser, ModelProfile, Option, RandomChooser, TopRankedChooser, load_profiles,
)
from coordination.agents.prompt import render_prompt

REQUEST = DecisionRequest(
    agent="alice",
    briefing="Your energy is high.",
    options=[
        Option(id=0, label="alice shares food with bob", score=5, is_default=True),
        Option(id=1, label="alice gathers wood", score=4),
        Option(id=2, label="alice rests", score=1),
    ],
)


def tool_model(*answers: dict) -> FunctionModel:
    """A fake model that answers through the output tool, one canned answer per call."""
    remaining = list(answers)

    def respond(messages, info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0]
        return ModelResponse(parts=[ToolCallPart(tool.name, json.dumps(remaining.pop(0)))])

    return FunctionModel(respond)


def native_model(answer: dict) -> FunctionModel:
    def respond(messages, info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart(json.dumps(answer))])

    return FunctionModel(respond)


def profile(**overrides) -> ModelProfile:
    return ModelProfile(**{"name": "fake", "provider": "test", "model": "fake", **overrides})


def test_llm_chooser_returns_the_models_choice_and_rationale():
    chooser = LLMChooser(profile(output_mode="tool"), model=tool_model({"rationale": "bob is tired", "choice_id": 0}))
    decision = chooser.choose(REQUEST)

    assert decision.choice_id == 0
    assert decision.rationale == "bob is tired"
    assert decision.model == "fake"
    assert decision.rue_chooser() == {"kind": "agent", "id": "alice", "note": "bob is tired"}


def test_native_output_mode():
    chooser = LLMChooser(profile(output_mode="native"), model=native_model({"rationale": "cold night", "choice_id": 1}))
    assert chooser.choose(REQUEST).choice_id == 1


def test_an_invalid_choice_is_retried_once():
    model = tool_model({"rationale": "?", "choice_id": 9}, {"rationale": "fine", "choice_id": 2})
    decision = LLMChooser(profile(output_mode="tool"), model=model).choose(REQUEST)

    assert decision.choice_id == 2
    retries = [p for m in decision.messages for p in m["parts"] if p["part_kind"] == "retry-prompt"]
    assert len(retries) == 1


def test_two_invalid_choices_pass_and_record_the_error():
    model = tool_model({"rationale": "?", "choice_id": 9}, {"rationale": "?", "choice_id": 7})
    decision = LLMChooser(profile(output_mode="tool"), model=model).choose(REQUEST)

    assert decision.passed
    assert decision.error


def test_scripted_choosers():
    assert TopRankedChooser().choose(REQUEST).choice_id == 0
    assert RandomChooser(seed=1).choose(REQUEST).choice_id in {0, 1, 2}


def test_scores_are_shown_only_when_requested():
    assert "suggested utility: 5" in render_prompt(REQUEST)
    assert "suggested utility" not in render_prompt(REQUEST.model_copy(update={"show_scores": False}))


def test_profiles_load_and_reject_unknown_keys(tmp_path):
    good = tmp_path / "good.toml"
    good.write_text('[profiles.local]\nprovider = "ollama"\nmodel = "qwen3.5:9b"\nthinking = "low"\n')
    profiles = load_profiles(good)
    assert profiles["local"].model_settings() == {"thinking": "low", "extra_body": {"reasoning_effort": "low"}}

    bad = tmp_path / "bad.toml"
    bad.write_text('[profiles.local]\nprovider = "ollama"\nmodel = "x"\ntemprature = 0.5\n')
    with pytest.raises(ValueError, match="temprature"):
        load_profiles(bad)


def test_ollama_thinking_off_maps_to_reasoning_effort_none():
    settings = profile(provider="ollama").model_settings()
    assert settings["extra_body"] == {"reasoning_effort": "none"}
    assert "extra_body" not in profile(provider="anthropic").model_settings()


def test_repo_models_toml_is_valid():
    assert "qwen-9b" in load_profiles("models.toml")
