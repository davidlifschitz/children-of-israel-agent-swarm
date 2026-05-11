from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coi_orchestrator import build_local_orchestrator, write_run_artifacts


SUPPORTED_TASK_TYPES = {"repo.bootstrap"}


@dataclass(slots=True)
class ScheduleOSExecutionAdapter:
    repo_root: Path
    output_dir: Path

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        task_type = str(task.get("task_type") or task.get("type") or "")
        if task_type not in SUPPORTED_TASK_TYPES:
            return {
                "status": "unsupported",
                "task_type": task_type or "unknown",
                "summary": f"Unsupported ScheduleOS task type: {task_type or 'unknown'}",
                "artifact_refs": [],
                "run_id": None,
            }
        orchestrator = build_local_orchestrator(self.repo_root, storage_root=self.output_dir / "storage")
        summary = orchestrator.execute_task(task)
        write_run_artifacts(orchestrator, summary["run_id"], summary, self.output_dir, task)
        return {
            "status": summary["status"],
            "task_type": summary["task_type"],
            "summary": summary["summary"],
            "artifact_refs": summary["artifact_refs"],
            "run_id": summary["run_id"],
            "event_count": summary["event_count"],
        }


def execute_scheduleos_task(
    task: dict[str, Any],
    repo_root: str | Path = ".",
    output_dir: str | Path = ".coi-scheduleos",
) -> dict[str, Any]:
    return ScheduleOSExecutionAdapter(Path(repo_root), Path(output_dir)).execute(task)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute a ScheduleOS-style task through the swarm adapter.")
    parser.add_argument("task", help="Path to a task JSON payload.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=".coi-scheduleos")
    args = parser.parse_args(argv)
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    result = execute_scheduleos_task(task, args.repo_root, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] != "unsupported" else 2


if __name__ == "__main__":
    raise SystemExit(main())
