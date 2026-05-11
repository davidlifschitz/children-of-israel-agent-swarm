from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
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
                return response.status < 500
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


def _normalise_output(output: object) -> dict[str, object]:
    if isinstance(output, dict):
        return output
    return {"summary": str(output), "raw_output": output, "confidence": 0.5}
