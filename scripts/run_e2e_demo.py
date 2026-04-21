#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from children_of_israel.intake.validate_task import validate_bootstrap_task


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def make_artifact(artifact_type: str, title: str, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    artifact_id = f"artifact_{artifact_type.replace('-', '_')}_{int(datetime.now().timestamp())}"
    return {
        "schema_version": "1.0.0",
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "title": title,
        "description": title,
        "origin_project": "children-of-israel-agent-swarm",
        "created_by": {"actor_type": "service", "actor_id": "children-of-israel-agent-swarm"},
        "created_at": utc_now(),
        "visibility": "private",
        "status": "active",
        "storage": {"storage_type": "inline", "mime_type": "application/json"},
        "content": {"format": "json", "json": payload, "summary": title},
        "metadata": {
            "project_id": "children-of-israel-agent-swarm",
            "task_id": task_id,
            "skill_id": "delegated-bootstrap-execution",
            "tags": ["bootstrap", "delegated-execution"],
        },
        "lineage": {"source_task_ids": [task_id], "source_artifact_ids": []},
        "relations": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the delegated bootstrap demo")
    parser.add_argument("--agentic-os", default="../agentic-os")
    parser.add_argument("--spec-to-repo", default="../spec-to-repo")
    parser.add_argument("--output", default="demo-output/delegated-bootstrap")
    args = parser.parse_args()

    agentic_os_root = Path(args.agentic_os).resolve()
    spec_to_repo_root = Path(args.spec_to_repo).resolve()
    output_root = Path(args.output).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    task_path = agentic_os_root / "examples" / "tasks" / "bootstrap-spec-to-repo.task.json"
    task = read_json(task_path)
    ok, errors = validate_bootstrap_task(task)
    if not ok:
        raise SystemExit("Task validation failed:\n- " + "\n- ".join(errors))

    delegated_output = output_root / "spec-to-repo-output"
    command = [
        "npm",
        "run",
        "bootstrap:demo",
        "--",
        "--agentic-os",
        str(agentic_os_root),
        "--output",
        str(delegated_output),
    ]
    delegated = subprocess.run(command, cwd=spec_to_repo_root, capture_output=True, text=True, check=True)
    delegated_summary = read_json(delegated_output / "summary.json")

    task_run_artifact = make_artifact(
        "task-run",
        "Delegated bootstrap task run",
        task["task_id"],
        {
            "status": "completed",
            "delegate": "spec-to-repo",
            "delegated_output_root": str(delegated_output),
            "summary": delegated_summary,
        },
    )
    execution_log_artifact = make_artifact(
        "execution-log",
        "Delegated bootstrap execution log",
        task["task_id"],
        {
            "command": command,
            "stdout": delegated.stdout,
            "stderr": delegated.stderr,
        },
    )
    result_bundle_artifact = make_artifact(
        "result-bundle",
        "Delegated bootstrap result bundle",
        task["task_id"],
        {
            "delegated_summary": delegated_summary,
            "delegated_artifact_paths": sorted(
                str(path.relative_to(output_root)) for path in delegated_output.rglob("*.json")
            ),
        },
    )

    result_bundle_artifact["lineage"]["source_artifact_ids"] = [
        task_run_artifact["artifact_id"],
        execution_log_artifact["artifact_id"],
    ]
    result_bundle_artifact["relations"] = [
        {"relation_type": "belongs_to", "target_kind": "project", "target_id": "spec-to-repo"},
        {"relation_type": "belongs_to", "target_kind": "task", "target_id": task["task_id"]},
    ]

    write_json(output_root / "task.json", task)
    write_json(output_root / "artifacts" / "task-run.artifact.json", task_run_artifact)
    write_json(output_root / "artifacts" / "execution-log.artifact.json", execution_log_artifact)
    write_json(output_root / "artifacts" / "result-bundle.artifact.json", result_bundle_artifact)
    write_json(
        output_root / "summary.json",
        {
            "ok": True,
            "task_id": task["task_id"],
            "delegated_project": "spec-to-repo",
            "artifacts": [
                task_run_artifact["artifact_type"],
                execution_log_artifact["artifact_type"],
                result_bundle_artifact["artifact_type"],
            ],
        },
    )

    print(json.dumps({"ok": True, "output_root": str(output_root), "task_id": task["task_id"]}, indent=2))


if __name__ == "__main__":
    main()
