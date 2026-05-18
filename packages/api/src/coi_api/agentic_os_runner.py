from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from coi_contracts import new_id, utc_now
from coi_orchestrator.agentic_os_engine import (
    JethroRepoDeliveryEngine,
    RunRequest,
    default_repo_root,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stream COI Agentic OS RunEvents as JSONL.")
    parser.add_argument("--request", required=True, help="Path to a RunRequest JSON file.")
    parser.add_argument("--repo-root", default=None, help="Children of Israel repo root.")
    parser.add_argument("--config", default=None, help="mission.yaml path.")
    args = parser.parse_args(argv)

    try:
        request = RunRequest.from_dict(_read_json(Path(args.request)))
        repo_root = Path(args.repo_root) if args.repo_root else default_repo_root()
        engine = JethroRepoDeliveryEngine(repo_root=repo_root, config_path=args.config)
        for event in engine.stream(request):
            print(json.dumps(event.to_dict(), sort_keys=True), flush=True)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI must convert failures into JSONL.
        print(json.dumps(_failure_event(exc), sort_keys=True), flush=True)
        return 1


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("RunRequest JSON must be an object")
    return data


def _failure_event(exc: Exception) -> dict[str, Any]:
    return {
        "event_id": new_id("agentic_os_event"),
        "run_id": "unknown",
        "type": "run.failed",
        "message": str(exc),
        "stage": None,
        "status": "failed",
        "actor": "coi_api",
        "tier": None,
        "model_policy": {},
        "payload": {"error_type": type(exc).__name__},
        "timestamp": utc_now(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
