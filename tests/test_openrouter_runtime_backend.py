from __future__ import annotations

import json
from typing import Any

from coi_contracts import RunStatus, Tier, WorkerRequest
from coi_orchestrator import agentic_os_engine as engine_module
from coi_runtime import OpenRouterRuntimeBackend, ProfileRoutingRuntimeBackend
from coi_runtime.profiles import load_tier_profiles


def _worker_request() -> WorkerRequest:
    return WorkerRequest(
        request_id="worker_openrouter_pytest",
        run_id="run_openrouter_pytest",
        tribe_id="moses",
        tier=Tier.ROOT,
        task_type="agentic_os.repo_delivery.intake",
        mandate="Clarify and route this task.",
        prompt="Return a JSON summary.",
        payload={"repo_path": "/tmp/repo", "stage": "intake"},
        runtime_profile_id="moses:openrouter_reasoning:openrouter:openrouter/auto",
    )


class _FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_openrouter_backend_sends_chat_completion_and_parses_json(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(
            {
                "model": "openai/gpt-5.2",
                "usage": {"prompt_tokens": 10, "completion_tokens": 7, "total_tokens": 17},
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "Moses clarified the task.",
                                    "confidence": 0.92,
                                    "artifacts": [],
                                }
                            )
                        }
                    }
                ],
            }
        )

    monkeypatch.setattr("coi_runtime.backends.request.urlopen", fake_urlopen)

    backend = OpenRouterRuntimeBackend(
        api_key="test-openrouter-key",
        model="openrouter/auto",
        referer="https://davidlifschitz.github.io",
        title="agentic-os",
        timeout_seconds=12,
    )
    result = backend.execute(_worker_request())

    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["timeout"] == 12
    assert captured["headers"]["Authorization"] == "Bearer test-openrouter-key"
    assert captured["headers"]["Http-referer"] == "https://davidlifschitz.github.io"
    assert captured["headers"]["X-openrouter-title"] == "agentic-os"
    assert captured["body"]["model"] == "openrouter/auto"
    assert captured["body"]["messages"][0]["role"] == "system"
    assert captured["body"]["messages"][1]["role"] == "user"
    assert result.status == RunStatus.SUCCEEDED
    assert result.worker_id == "moses:openrouter"
    assert result.output["summary"] == "Moses clarified the task."
    assert result.output["_runtime"]["provider"] == "openrouter"
    assert result.output["_runtime"]["model"] == "openai/gpt-5.2"
    assert result.output["_runtime"]["usage"]["total_tokens"] == 17


def test_openrouter_backend_reports_missing_api_key_without_http_call(monkeypatch):
    def fail_urlopen(*_: object, **__: object):
        raise AssertionError("OpenRouter backend should not make HTTP requests without an API key")

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("coi_runtime.backends.request.urlopen", fail_urlopen)

    result = OpenRouterRuntimeBackend(api_key="").execute(_worker_request())

    assert result.status == RunStatus.FAILED
    assert result.failure is not None
    assert result.failure.code == "openrouter_missing_api_key"
    assert result.failure.retryable is False


def test_default_backend_selects_openrouter_when_requested(monkeypatch):
    monkeypatch.setenv("AGENTIC_OS_COI_BACKEND", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("AGENTIC_OS_OPENROUTER_MODEL", "openrouter/auto")

    backend = engine_module._default_backend()

    assert backend.name == "openrouter"


def test_default_backend_auto_uses_profile_routing(monkeypatch):
    monkeypatch.delenv("AGENTIC_OS_COI_BACKEND", raising=False)

    backend = engine_module._default_backend()

    assert backend.name == "profile-routing"


def test_profile_routing_openrouter_fallback_is_explicit(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    backend = ProfileRoutingRuntimeBackend(openrouter=OpenRouterRuntimeBackend(api_key=""))

    result = backend.execute(_worker_request())

    assert result.status == RunStatus.SUCCEEDED
    assert result.worker_id == "moses:openrouter-mock-fallback"
    assert result.output["_runtime"]["provider"] == "openrouter"
    assert result.output["_runtime"]["fallback"] == "mock"
    assert result.output["_runtime"]["reason"] == "provider_unavailable"


def test_mission_routes_moses_to_openrouter_reasoning_and_keeps_leaf_tiers_local():
    profiles = load_tier_profiles("config/mission.yaml")

    assert profiles["moses"].model_class == "openrouter_reasoning"
    assert profiles["moses"].provider == "openrouter"
    assert profiles["moses"].model == "openrouter/auto"
    assert profiles["reuben"].provider == "ollama"
    assert profiles["reuben"].model_class == "leaf_executor"
