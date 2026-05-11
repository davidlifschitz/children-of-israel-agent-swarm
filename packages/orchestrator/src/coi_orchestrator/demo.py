from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .artifacts import write_run_artifacts
from .orchestrator import build_local_orchestrator


def run_demo(repo_root: str | Path, task_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    repo = Path(repo_root)
    out = Path(output_dir)
    task = json.loads(Path(task_path).read_text(encoding="utf-8"))
    orchestrator = build_local_orchestrator(repo, storage_root=out / "storage")
    summary = orchestrator.execute_task(task)
    run_id = summary["run_id"]
    write_run_artifacts(orchestrator, run_id, summary, out, task)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local mock Children of Israel swarm task.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing law/ and config/.")
    parser.add_argument("--task", default="examples/tasks/local_bootstrap.task.json", help="Task payload JSON.")
    parser.add_argument("--output-dir", default=".coi-demo", help="Directory for local artifacts.")
    args = parser.parse_args(argv)
    summary = run_demo(args.repo_root, args.task, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
