from __future__ import annotations

from pathlib import Path

import pytest

from coi_orchestrator import agentic_os_engine as engine_module
from coi_orchestrator.agentic_os_engine import JethroRepoDeliveryEngine, RunRequest
from coi_runtime import MockRuntimeBackend


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_DELIVERY_STAGE_NAMES = ["intake", "spec", "plan", "implementation", "verification", "pr"]
REQUIRED_GATES = ["spec", "implementation", "pr"]


def test_fallback_contract_is_explicit_when_langgraph_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(engine_module, "LANGGRAPH_AVAILABLE", False)
    monkeypatch.setattr(engine_module, "StateGraph", None)

    events = list(_engine().stream(_request(tmp_path)))

    fallback = next(event for event in events if event.type == "runtime.fallback")
    assert events[0].payload["execution_path"] == "deterministic_fallback"
    assert events[0].payload["langgraph_available"] is False
    assert fallback.payload == {
        "concern": "langgraph_dependency_missing",
        "dependency": "langgraph",
        "install_extra": "langgraph",
        "install_command": "uv sync --extra dev --extra langgraph",
    }
    assert _completed_stage_names(events) == ["intake"]
    assert _approval_gates(events) == ["spec"]
    assert events[-1].payload["pending_approval_gates"] == ["spec"]


def test_langgraph_path_runs_repo_delivery_graph_when_installed(tmp_path):
    pytest.importorskip("langgraph.graph")
    if not engine_module._langgraph_available():
        pytest.skip("LangGraph import is not active for this interpreter.")

    events = list(_engine().stream(_request(tmp_path)))

    assert events[0].payload["execution_path"] == "langgraph"
    assert events[0].payload["langgraph_available"] is True
    assert not [event for event in events if event.type == "runtime.fallback"]
    assert _completed_stage_names(events) == ["intake"]
    assert _approval_gates(events) == ["spec"]
    assert events[-1].payload["pending_approval_gates"] == ["spec"]


def _engine() -> JethroRepoDeliveryEngine:
    return JethroRepoDeliveryEngine(
        repo_root=REPO_ROOT,
        backend=MockRuntimeBackend(name="agentic-os-test-mock"),
    )


def _request(tmp_path: Path) -> RunRequest:
    return RunRequest(
        run_id="run_pytest_agentic_os_langgraph",
        goal="Prepare a repo delivery plan without live model calls.",
        repo_path=str(tmp_path / "target-repo"),
        mode="deterministic",
        approval_policy={stage: "required" for stage in REQUIRED_GATES},
        metadata={"source": "pytest"},
    )


def _completed_stage_names(events):
    return [event.stage for event in events if event.type == "stage.completed"]


def _approval_gates(events):
    return [event.payload["gate"] for event in events if event.type == "approval.waiting"]
