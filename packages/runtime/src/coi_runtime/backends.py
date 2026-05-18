from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Protocol
from urllib import error, request

from coi_contracts import RunStatus, RuntimeFailure, WorkerRequest, WorkerResult


class RuntimeBackend(Protocol):
    name: str

    def available(self) -> bool: ...
    def execute(self, worker_request: WorkerRequest) -> WorkerResult: ...


@dataclass(slots=True)
class MockRuntimeBackend:
    name: str = "mock"

    def available(self) -> bool:
        return True

    def execute(self, worker_request: WorkerRequest) -> WorkerResult:
        output = {
            "summary": f"Mock execution for {worker_request.task_type}",
            "tribe_id": worker_request.tribe_id,
            "tier": worker_request.tier.value,
            "mandate": worker_request.mandate,
            "payload_keys": sorted(worker_request.payload.keys()),
            "confidence": 1.0,
        }
        return WorkerResult(
            request_id=worker_request.request_id,
            run_id=worker_request.run_id,
            worker_id=f"{worker_request.tribe_id}:mock",
            status=RunStatus.SUCCEEDED,
            output=output,
        )


@dataclass(slots=True)
class OllamaRuntimeBackend:
    model: str = "llama3.2"
    endpoint: str = "http://127.0.0.1:11434/api/generate"
    timeout_seconds: float = 30.0
    name: str = "ollama"

    def available(self) -> bool:
        probe_url = self.endpoint.rsplit("/", 1)[0].rsplit("/", 1)[0] + "/api/tags"
        try:
            with request.urlopen(probe_url, timeout=2.0) as response:
                if response.status >= 500:
                    return False
                payload = json.loads(response.read().decode("utf-8") or "{}")
                models = payload.get("models", [])
                return any(
                    item.get("name") == self.model or item.get("model") == self.model
                    for item in models
                    if isinstance(item, dict)
                )
        except (OSError, error.URLError):
            return False

    def execute(self, worker_request: WorkerRequest) -> WorkerResult:
        prompt = {
            "mandate": worker_request.mandate,
            "task_type": worker_request.task_type,
            "tribe_id": worker_request.tribe_id,
            "prompt": worker_request.prompt,
            "payload": worker_request.payload,
            "required_format": {
                "summary": "string",
                "confidence": "number",
                "artifacts": "array",
            },
        }
        body = json.dumps(
            {"model": self.model, "prompt": json.dumps(prompt), "stream": False, "format": "json"}
        ).encode("utf-8")
        try:
            req = request.Request(
                self.endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - convert any adapter failure into a typed runtime result.
            return WorkerResult(
                request_id=worker_request.request_id,
                run_id=worker_request.run_id,
                worker_id=f"{worker_request.tribe_id}:ollama",
                status=RunStatus.FAILED,
                failure=RuntimeFailure(
                    code="ollama_unavailable",
                    message=str(exc),
                    retryable=True,
                    details={"endpoint": self.endpoint, "model": self.model},
                ),
            )
        response_text = raw.get("response", "{}")
        try:
            output = json.loads(response_text) if isinstance(response_text, str) else response_text
        except json.JSONDecodeError:
            output = {"summary": str(response_text), "confidence": 0.5}
        return WorkerResult(
            request_id=worker_request.request_id,
            run_id=worker_request.run_id,
            worker_id=f"{worker_request.tribe_id}:ollama",
            status=RunStatus.SUCCEEDED,
            output=_normalise_output(output),
        )


@dataclass(slots=True)
class OpenRouterRuntimeBackend:
    model: str = "openrouter/auto"
    endpoint: str = "https://openrouter.ai/api/v1/chat/completions"
    api_key: str | None = None
    timeout_seconds: float = 60.0
    referer: str | None = None
    title: str = "children-of-israel-agent-swarm"
    name: str = "openrouter"

    def available(self) -> bool:
        return bool(self._api_key())

    def for_model(self, model: str) -> "OpenRouterRuntimeBackend":
        return OpenRouterRuntimeBackend(
            model=model or self.model,
            endpoint=self.endpoint,
            api_key=self.api_key,
            timeout_seconds=self.timeout_seconds,
            referer=self.referer,
            title=self.title,
            name=self.name,
        )

    def execute(self, worker_request: WorkerRequest) -> WorkerResult:
        api_key = self._api_key()
        if not api_key:
            return WorkerResult(
                request_id=worker_request.request_id,
                run_id=worker_request.run_id,
                worker_id=f"{worker_request.tribe_id}:openrouter",
                status=RunStatus.FAILED,
                failure=RuntimeFailure(
                    code="openrouter_missing_api_key",
                    message="OPENROUTER_API_KEY is required for the OpenRouter runtime backend.",
                    retryable=False,
                    details={"endpoint": self.endpoint, "model": self.model},
                ),
            )

        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a Children of Israel runtime worker. "
                            "Return one JSON object with summary, confidence, and artifacts."
                        ),
                    },
                    {"role": "user", "content": json.dumps(_worker_prompt(worker_request))},
                ],
                "temperature": 0,
            }
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if self.referer:
            headers["HTTP-Referer"] = self.referer
        if self.title:
            headers["X-OpenRouter-Title"] = self.title

        try:
            req = request.Request(self.endpoint, data=body, headers=headers, method="POST")
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            return _failed_openrouter_result(worker_request, self, _http_error_message(exc), retryable=True)
        except Exception as exc:  # noqa: BLE001 - adapter failures become typed runtime failures.
            return _failed_openrouter_result(worker_request, self, str(exc), retryable=True)

        output = _normalise_output(_openrouter_output(raw))
        output["_runtime"] = {
            "provider": "openrouter",
            "model": raw.get("model", self.model) if isinstance(raw, dict) else self.model,
            "usage": raw.get("usage", {}) if isinstance(raw, dict) else {},
        }
        return WorkerResult(
            request_id=worker_request.request_id,
            run_id=worker_request.run_id,
            worker_id=f"{worker_request.tribe_id}:openrouter",
            status=RunStatus.SUCCEEDED,
            output=output,
        )

    def _api_key(self) -> str:
        return (self.api_key if self.api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")).strip()


@dataclass(slots=True)
class HermesRuntimeAdapter:
    binary: str = "hermes"
    timeout_seconds: float = 120.0
    name: str = "hermes"

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def execute(self, worker_request: WorkerRequest) -> WorkerResult:
        if not self.available():
            return WorkerResult(
                request_id=worker_request.request_id,
                run_id=worker_request.run_id,
                worker_id=f"{worker_request.tribe_id}:hermes",
                status=RunStatus.FAILED,
                failure=RuntimeFailure(
                    code="hermes_unavailable",
                    message=f"Hermes binary '{self.binary}' is not on PATH.",
                    retryable=False,
                ),
            )
        payload = json.dumps(
            {
                "request_id": worker_request.request_id,
                "run_id": worker_request.run_id,
                "tribe_id": worker_request.tribe_id,
                "task_type": worker_request.task_type,
                "mandate": worker_request.mandate,
                "prompt": worker_request.prompt,
                "payload": worker_request.payload,
            }
        )
        try:
            completed = subprocess.run(
                [self.binary, "--no-learn", "--json-output", "--non-interactive", payload],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            return WorkerResult(
                request_id=worker_request.request_id,
                run_id=worker_request.run_id,
                worker_id=f"{worker_request.tribe_id}:hermes",
                status=RunStatus.FAILED,
                failure=RuntimeFailure(code="hermes_error", message=str(exc), retryable=True),
            )
        if completed.returncode != 0:
            return WorkerResult(
                request_id=worker_request.request_id,
                run_id=worker_request.run_id,
                worker_id=f"{worker_request.tribe_id}:hermes",
                status=RunStatus.FAILED,
                failure=RuntimeFailure(
                    code="hermes_failed",
                    message=completed.stderr.strip() or "Hermes returned non-zero status.",
                    retryable=True,
                    details={"returncode": completed.returncode},
                ),
            )
        try:
            output = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            output = {"summary": completed.stdout.strip(), "confidence": 0.5}
        return WorkerResult(
            request_id=worker_request.request_id,
            run_id=worker_request.run_id,
            worker_id=f"{worker_request.tribe_id}:hermes",
            status=RunStatus.SUCCEEDED,
            output=_normalise_output(output),
        )


@dataclass(slots=True)
class ProfileRoutingRuntimeBackend:
    openrouter: OpenRouterRuntimeBackend = field(default_factory=OpenRouterRuntimeBackend)
    mock: MockRuntimeBackend = field(default_factory=lambda: MockRuntimeBackend(name="profile-mock-fallback"))
    ollama_endpoint: str = "http://127.0.0.1:11434/api/generate"
    ollama_timeout_seconds: float = 30.0
    name: str = "profile-routing"

    def available(self) -> bool:
        return True

    def execute(self, worker_request: WorkerRequest) -> WorkerResult:
        profile = _parse_runtime_profile_id(worker_request.runtime_profile_id)
        provider = profile.get("provider", "")
        model = profile.get("model", "")
        if provider == "openrouter":
            backend = self.openrouter.for_model(model)
            return (
                backend.execute(worker_request)
                if backend.available()
                else _provider_mock_fallback(worker_request, self.mock, provider, model)
            )
        if provider == "ollama":
            backend = OllamaRuntimeBackend(
                model=model or "llama3.2",
                endpoint=self.ollama_endpoint,
                timeout_seconds=self.ollama_timeout_seconds,
            )
            return (
                backend.execute(worker_request)
                if backend.available()
                else _provider_mock_fallback(worker_request, self.mock, provider, model)
            )
        return _provider_mock_fallback(worker_request, self.mock, provider or "unknown", model)


def _normalise_output(output: object) -> dict[str, object]:
    if isinstance(output, dict):
        return output
    return {"summary": str(output), "raw_output": output, "confidence": 0.5}


def _worker_prompt(worker_request: WorkerRequest) -> dict[str, object]:
    return {
        "mandate": worker_request.mandate,
        "task_type": worker_request.task_type,
        "tribe_id": worker_request.tribe_id,
        "tier": worker_request.tier.value,
        "prompt": worker_request.prompt,
        "payload": worker_request.payload,
        "required_format": {
            "summary": "string",
            "confidence": "number",
            "artifacts": "array",
        },
    }


def _openrouter_output(raw: object) -> object:
    if not isinstance(raw, dict):
        return {"summary": str(raw), "confidence": 0.5}
    choices = raw.get("choices")
    first = choices[0] if isinstance(choices, list) and choices else {}
    message = first.get("message") if isinstance(first, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        content = "\n".join(str(part.get("text", part)) for part in content if isinstance(part, dict))
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"summary": content, "confidence": 0.5}
    return {"summary": "", "confidence": 0.0}


def _failed_openrouter_result(
    worker_request: WorkerRequest,
    backend: OpenRouterRuntimeBackend,
    message: str,
    *,
    retryable: bool,
) -> WorkerResult:
    return WorkerResult(
        request_id=worker_request.request_id,
        run_id=worker_request.run_id,
        worker_id=f"{worker_request.tribe_id}:openrouter",
        status=RunStatus.FAILED,
        failure=RuntimeFailure(
            code="openrouter_unavailable",
            message=message,
            retryable=retryable,
            details={"endpoint": backend.endpoint, "model": backend.model},
        ),
    )


def _provider_mock_fallback(
    worker_request: WorkerRequest,
    mock: MockRuntimeBackend,
    provider: str,
    model: str,
) -> WorkerResult:
    result = mock.execute(worker_request)
    output = dict(result.output)
    output["_runtime"] = {
        "provider": provider,
        "model": model,
        "fallback": "mock",
        "reason": "provider_unavailable",
    }
    return WorkerResult(
        request_id=result.request_id,
        run_id=result.run_id,
        worker_id=f"{worker_request.tribe_id}:{provider}-mock-fallback",
        status=result.status,
        output=output,
        events=result.events,
        failure=result.failure,
    )


def _http_error_message(exc: error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
    except Exception:  # noqa: BLE001 - best effort diagnostic.
        body = ""
    return body or str(exc)


def _parse_runtime_profile_id(profile_id: str | None) -> dict[str, str]:
    if not profile_id:
        return {}
    parts = profile_id.split(":", 3)
    if len(parts) != 4:
        return {}
    tribe_id, model_class, provider, model = parts
    return {
        "tribe_id": tribe_id,
        "model_class": model_class,
        "provider": provider,
        "model": model,
    }
