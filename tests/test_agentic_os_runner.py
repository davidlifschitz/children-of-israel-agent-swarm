from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from coi_runtime.profiles import load_tier_profiles


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_agentic_os_runner_streams_jethro_repo_delivery_events(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "run_id": "run_pytest_agentic_os",
                "goal": "Prepare a repo delivery plan without pushing.",
                "repo_path": str(tmp_path / "target-repo"),
                "mode": "deterministic",
                "approval_policy": {
                    "implementation": "required",
                    "pr": "required",
                },
                "metadata": {"source": "pytest"},
            }
        )
    )

    completed = subprocess.run(
        [sys.executable, "-m", "coi_api.agentic_os_runner", "--request", str(request_path)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env={**os.environ, "AGENTIC_OS_COI_BACKEND": "mock"},
    )

    events = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    event_types = [event["type"] for event in events]
    stages = {event.get("stage") for event in events}
    approval_gates = [
        event["payload"]["gate"] for event in events if event["type"] == "approval.waiting"
    ]
    dispatched = [event for event in events if event["type"] == "worker.dispatched"]

    assert event_types[0] == "run.started"
    assert {"intake", "spec", "plan"} <= stages
    assert approval_gates == ["implementation"]
    assert dispatched
    assert all(event["stage"] != "implementation" for event in dispatched)
    assert all(event["model_policy"]["provider"] == "ollama" for event in dispatched)
    completed_artifact_paths = [
        event["payload"]["artifact"]["relative_path"]
        for event in events
        if event["type"] == "stage.completed"
    ]
    assert ".agentic-os/runs/run_pytest_agentic_os/spec.md" in completed_artifact_paths
    assert events[-1]["type"] == "run.result"
    assert events[-1]["payload"]["status"] == "waiting_approval"
    assert events[-1]["payload"]["pending_approval_gates"] == ["implementation"]


def test_model_policy_resolves_jethro_tiers_and_preserves_legacy_routing():
    profiles = load_tier_profiles(REPO_ROOT / "config" / "mission.yaml")

    assert profiles["moses"].tier.value == "root"
    assert profiles["judah"].model_class == "senior_judge"
    assert profiles["simeon"].model_class == "compliance"
    assert profiles["reuben"].model_class == "leaf_executor"
    assert profiles["judah"].provider == "ollama"
    assert profiles["judah"].model == "llama3.2"
    assert profiles["judah"].profile_id == "judah:senior_judge:ollama:llama3.2"
