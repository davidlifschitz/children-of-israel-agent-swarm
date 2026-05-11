from __future__ import annotations

import json
import os
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

import pytest

from coi_api import create_handler
from coi_integrations import execute_scheduleos_task
from coi_orchestrator import build_local_orchestrator
from coi_orchestrator.demo import run_demo
from coi_orchestrator.orchestrator import build_ollama_orchestrator
from coi_runtime import OllamaRuntimeBackend


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK = {
    "id": "test-bootstrap",
    "task_type": "repo.bootstrap",
    "source": "pytest",
    "mandate": "Validate the local execution path.",
    "payload": {"repo": "children-of-israel-agent-swarm"},
}


def test_orchestrator_runs_golden_path_with_mock_runtime(tmp_path):
    orchestrator = build_local_orchestrator(REPO_ROOT, storage_root=tmp_path)
    summary = orchestrator.execute_task(dict(TASK))

    assert summary["status"] == "succeeded"
    assert summary["task_type"] == "repo.bootstrap"
    assert summary["artifact_refs"] == [
        f"artifacts/{summary['run_id']}/task-run.artifact.json",
        f"artifacts/{summary['run_id']}/execution-log.artifact.json",
        f"artifacts/{summary['run_id']}/result-bundle.artifact.json",
    ]
    events = orchestrator.get_events(summary["run_id"])
    event_types = [event.event_type.value for event in events]
    assert "runtime.fallback" not in event_types
    assert "checkpoint.saved" in event_types
    assert "run.succeeded" in event_types
    assert summary["event_count"] == len(events)


def test_hermes_branch_is_opt_in_and_falls_back_when_unavailable(tmp_path):
    orchestrator = build_local_orchestrator(REPO_ROOT, storage_root=tmp_path, use_hermes=True)
    summary = orchestrator.execute_task(dict(TASK))
    event_types = [event.event_type.value for event in orchestrator.get_events(summary["run_id"])]

    assert summary["status"] == "succeeded"
    assert "runtime.fallback" in event_types


def test_invalid_payload_is_blocked_not_crashed(tmp_path):
    orchestrator = build_local_orchestrator(REPO_ROOT, storage_root=tmp_path)
    summary = orchestrator.execute_task({**TASK, "payload": ["not", "an", "object"]})

    assert summary["status"] == "blocked"
    assert any(verdict["rule_id"] == "P-IV-003" for verdict in summary["law_verdicts"])


def test_local_demo_writes_artifacts(tmp_path):
    task_path = REPO_ROOT / "examples" / "tasks" / "local_bootstrap.task.json"
    summary = run_demo(REPO_ROOT, task_path, tmp_path)

    assert summary["status"] == "succeeded"
    assert (tmp_path / "summary.json").exists()
    for ref in summary["artifact_refs"]:
        assert (tmp_path / ref).exists()


def test_scheduleos_adapter_result_shape_and_unsupported_task(tmp_path):
    result = execute_scheduleos_task(dict(TASK), REPO_ROOT, tmp_path)
    unsupported = execute_scheduleos_task(
        {"task_type": "unknown", "mandate": "No-op", "source": "pytest"},
        REPO_ROOT,
        tmp_path,
    )

    assert result["status"] == "succeeded"
    assert result["run_id"]
    assert result["artifact_refs"]
    for ref in result["artifact_refs"]:
        assert (tmp_path / ref).exists()
    assert unsupported["status"] == "unsupported"


def test_api_health_run_events_and_summary(tmp_path):
    handler = create_handler(REPO_ROOT, tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        health = _get_json(f"{base}/health")
        assert health["ready"] is True
        created = _post_json(f"{base}/runs", TASK)
        run_id = created["run_id"]
        fetched = _get_json(f"{base}/runs/{run_id}")
        events = _get_json(f"{base}/runs/{run_id}/events")
        summary = _get_json(f"{base}/runs/{run_id}/summary")
        missing_events = _http_status(f"{base}/runs/missing/events")
        bad_json = _post_status(f"{base}/runs", b"not-json")
    finally:
        server.shutdown()
        server.server_close()

    assert fetched["run_id"] == run_id
    assert len(events["events"]) >= 5
    assert summary["status"] == "succeeded"
    assert missing_events == 404
    assert bad_json == 400


@pytest.mark.skipif(os.environ.get("COI_RUN_LIVE_OLLAMA") != "1", reason="live Ollama path is opt-in")
def test_live_ollama_backend_availability_or_typed_failure(tmp_path):
    backend = OllamaRuntimeBackend(timeout_seconds=5)
    orchestrator = build_ollama_orchestrator(REPO_ROOT, storage_root=tmp_path)
    summary = orchestrator.execute_task(dict(TASK))

    if backend.available():
        assert summary["status"] in {"succeeded", "blocked"}
    else:
        assert summary["status"] in {"failed", "blocked"}
        assert summary["law_verdicts"]


def _get_json(url: str):
    with request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_status(url: str) -> int:
    try:
        with request.urlopen(url, timeout=5) as response:
            return response.status
    except error.HTTPError as exc:
        return exc.code


def _post_status(url: str, body: bytes) -> int:
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=5) as response:
            return response.status
    except error.HTTPError as exc:
        return exc.code
