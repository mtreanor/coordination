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


def overloaded_then(answer: dict, failures: int) -> FunctionModel:
    """A fake model that fails with HTTP 503 a few times, then answers."""
    from pydantic_ai.exceptions import ModelHTTPError

    calls = {"n": 0}

    def respond(messages, info: AgentInfo) -> ModelResponse:
        calls["n"] += 1
        if calls["n"] <= failures:
            raise ModelHTTPError(503, "fake", {"error": "overloaded"})
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, json.dumps(answer))])

    return FunctionModel(respond)


def test_transient_provider_errors_are_retried():
    model = overloaded_then({"rationale": "ok", "choice_id": 1}, failures=2)
    chooser = LLMChooser(profile(output_mode="tool"), model=model, backoff_s=0)
    assert chooser.choose(REQUEST).choice_id == 1


def test_a_persistent_provider_error_stops_the_run():
    from pydantic_ai.exceptions import ModelHTTPError

    model = overloaded_then({"rationale": "ok", "choice_id": 1}, failures=10)
    chooser = LLMChooser(profile(output_mode="tool"), model=model, api_attempts=3, backoff_s=0)
    with pytest.raises(ModelHTTPError):
        chooser.choose(REQUEST)


def test_the_providers_requested_delay_is_honored():
    from pydantic_ai.exceptions import ModelHTTPError

    from coordination.agents.llm import requested_delay

    google = ModelHTTPError(429, "m", {"error": {"details": [{"retryDelay": "22s"}]}})
    assert requested_delay(google) == 22.0
    assert requested_delay(ModelHTTPError(429, "m", None, headers={"retry-after": "7"})) == 7.0
    assert requested_delay(ModelHTTPError(503, "m", None)) is None


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


def test_usage_cost_becomes_a_plain_number():
    from decimal import Decimal

    from pydantic_ai.usage import RunUsage

    from coordination.agents.llm import usage_dict

    assert usage_dict(RunUsage(input_tokens=10, cost=Decimal("0.0012")))["cost"] == 0.0012


def test_decision_log_writes_json_lines(tmp_path):
    from coordination.agents import Decision, DecisionLog

    log = DecisionLog(tmp_path / "decisions.jsonl")
    log.write(REQUEST, Decision(choice_id=1, chooser_kind="agent", usage={"cost": 0.5}), tick=3)
    record = json.loads(log.path.read_text())
    assert record["tick"] == 3 and record["decision"]["choice_id"] == 1


def test_anthropic_workspace_header_comes_from_the_environment(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_WORKSPACE_ID", raising=False)
    assert "extra_headers" not in profile(provider="anthropic").model_settings()
    monkeypatch.setenv("ANTHROPIC_WORKSPACE_ID", "wrkspc_123")
    headers = profile(provider="anthropic").model_settings()["extra_headers"]
    assert headers == {"anthropic-workspace-id": "wrkspc_123"}


def test_repo_models_toml_is_valid():
    assert "qwen-9b" in load_profiles("models.toml")
