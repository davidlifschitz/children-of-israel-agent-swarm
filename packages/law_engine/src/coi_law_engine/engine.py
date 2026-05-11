from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from coi_contracts import (
    LawSeverity,
    LawVerdict,
    LawVerdictKind,
    RunStatus,
    WorkerResult,
    new_id,
)

from .registry import LawRegistry


@dataclass(slots=True)
class LawEngine:
    registry: LawRegistry

    def evaluate_task(self, run_id: str, task: dict[str, Any]) -> list[LawVerdict]:
        verdicts: list[LawVerdict] = []
        mandate = str(task.get("mandate") or "").strip()
        task_type = str(task.get("task_type") or task.get("type") or "").strip()
        if not mandate:
            verdicts.append(
                _verdict(
                    run_id,
                    LawVerdictKind.HARD_BLOCK,
                    LawSeverity.BLOCKER,
                    "C3",
                    "Task is missing an explicit mandate.",
                    {"field": "mandate"},
                )
            )
        if not task_type:
            verdicts.append(
                _verdict(
                    run_id,
                    LawVerdictKind.HARD_BLOCK,
                    LawSeverity.BLOCKER,
                    "P-IV-003",
                    "Task is missing a task_type.",
                    {"field": "task_type"},
                )
            )
        if "payload" in task and not isinstance(task.get("payload"), Mapping):
            verdicts.append(
                _verdict(
                    run_id,
                    LawVerdictKind.HARD_BLOCK,
                    LawSeverity.BLOCKER,
                    "P-IV-003",
                    "Task payload must be a JSON object when provided.",
                    {"field": "payload", "received_type": type(task.get("payload")).__name__},
                )
            )
        if not task.get("source"):
            verdicts.append(
                _verdict(
                    run_id,
                    LawVerdictKind.ADVISORY,
                    LawSeverity.WARNING,
                    "P-IV-002",
                    "Task has no source metadata; local execution will continue with a warning.",
                    {"field": "source"},
                )
            )
        if not verdicts:
            verdicts.append(
                _verdict(
                    run_id,
                    LawVerdictKind.PASS,
                    LawSeverity.INFO,
                    "C1",
                    "Task intake satisfies the initial hard constraints.",
                )
            )
        return verdicts

    def evaluate_worker_result(self, result: WorkerResult) -> list[LawVerdict]:
        verdicts: list[LawVerdict] = []
        if result.status == RunStatus.FAILED:
            verdicts.append(
                _verdict(
                    result.run_id,
                    LawVerdictKind.HARD_BLOCK,
                    LawSeverity.BLOCKER,
                    "C6",
                    "Worker failed and must be escalated or recovered.",
                    {"failure": result.failure.message if result.failure else "unknown"},
                )
            )
        if not result.output:
            verdicts.append(
                _verdict(
                    result.run_id,
                    LawVerdictKind.ADVISORY,
                    LawSeverity.WARNING,
                    "P-UH-005",
                    "Worker output is empty.",
                    {"worker_id": result.worker_id},
                )
            )
        elif "confidence" not in result.output:
            verdicts.append(
                _verdict(
                    result.run_id,
                    LawVerdictKind.ADVISORY,
                    LawSeverity.WARNING,
                    "P-UH-002",
                    "Worker output has no confidence score.",
                    {"worker_id": result.worker_id},
                )
            )
        if not verdicts:
            verdicts.append(
                _verdict(
                    result.run_id,
                    LawVerdictKind.PASS,
                    LawSeverity.INFO,
                    "C5",
                    "Worker output is structured enough for downstream use.",
                    {"worker_id": result.worker_id},
                )
            )
        return verdicts


def _verdict(
    run_id: str,
    kind: LawVerdictKind,
    severity: LawSeverity,
    rule_id: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> LawVerdict:
    return LawVerdict(
        verdict_id=new_id("verdict"),
        run_id=run_id,
        kind=kind,
        severity=severity,
        rule_id=rule_id,
        message=message,
        details=details or {},
    )
