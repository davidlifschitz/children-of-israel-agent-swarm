from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from coi_contracts import to_jsonable


def write_run_artifacts(orchestrator: Any, run_id: str, summary: dict[str, Any], output_dir: str | Path, task: dict[str, Any] | None = None) -> None:
    out = Path(output_dir)
    artifacts = out / "artifacts" / run_id
    artifacts.mkdir(parents=True, exist_ok=True)
    run = orchestrator.get_run(run_id)
    events = orchestrator.get_events(run_id)
    if task is not None:
        (out / "task.json").write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_json(artifacts / "task-run.artifact.json", {"kind": "task-run", "run": to_jsonable(run)})
    _write_json(
        artifacts / "execution-log.artifact.json",
        {"kind": "execution-log", "events": [to_jsonable(event) for event in events]},
    )
    _write_json(
        artifacts / "result-bundle.artifact.json",
        {"kind": "result-bundle", "summary": summary, "outputs": summary.get("worker_results", [])},
    )
    _write_json(out / "summary.json", summary)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
