from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


JsonDict = dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class Tier(StrEnum):
    ROOT = "root"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_4 = "tier_4"


class EventType(StrEnum):
    RUN_CREATED = "run.created"
    RUN_STARTED = "run.started"
    WORKER_DISPATCHED = "worker.dispatched"
    WORKER_COMPLETED = "worker.completed"
    LAW_VERDICT = "law.verdict"
    CHECKPOINT_SAVED = "checkpoint.saved"
    PRECEDENT_RECORDED = "precedent.recorded"
    ESCALATED = "run.escalated"
    FALLBACK = "runtime.fallback"
    RUN_SUCCEEDED = "run.succeeded"
    RUN_FAILED = "run.failed"


class LawVerdictKind(StrEnum):
    PASS = "pass"
    HARD_BLOCK = "hard_block"
    ADVISORY = "advisory"


class LawSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


@dataclass(slots=True)
class RuntimeFailure:
    code: str
    message: str
    retryable: bool = False
    details: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class Run:
    run_id: str
    task_type: str
    mandate: str
    status: RunStatus = RunStatus.PENDING
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: JsonDict = field(default_factory=dict)
    summary: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class WorkerRequest:
    request_id: str
    run_id: str
    tribe_id: str
    tier: Tier
    task_type: str
    mandate: str
    prompt: str
    payload: JsonDict = field(default_factory=dict)
    runtime_profile_id: str | None = None


@dataclass(slots=True)
class WorkerResult:
    request_id: str
    run_id: str
    worker_id: str
    status: RunStatus
    output: JsonDict = field(default_factory=dict)
    events: list[JsonDict] = field(default_factory=list)
    failure: RuntimeFailure | None = None


@dataclass(slots=True)
class Event:
    event_id: str
    run_id: str
    event_type: EventType
    message: str
    created_at: str = field(default_factory=utc_now)
    actor: str = "system"
    payload: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class LawVerdict:
    verdict_id: str
    run_id: str
    kind: LawVerdictKind
    severity: LawSeverity
    rule_id: str
    message: str
    created_at: str = field(default_factory=utc_now)
    details: JsonDict = field(default_factory=dict)

    @property
    def blocks_execution(self) -> bool:
        return self.kind == LawVerdictKind.HARD_BLOCK


@dataclass(slots=True)
class CheckpointRecord:
    checkpoint_id: str
    run_id: str
    stage: str
    state: JsonDict
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class PrecedentRecord:
    precedent_id: str
    run_id: str
    verdict_id: str
    rule_id: str
    ruling: str
    created_at: str = field(default_factory=utc_now)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def run_from_dict(data: JsonDict) -> Run:
    return Run(
        run_id=str(data["run_id"]),
        task_type=str(data["task_type"]),
        mandate=str(data.get("mandate", "")),
        status=RunStatus(data.get("status", RunStatus.PENDING)),
        created_at=str(data.get("created_at") or utc_now()),
        updated_at=str(data.get("updated_at") or utc_now()),
        metadata=dict(data.get("metadata") or {}),
        summary=dict(data.get("summary") or {}),
    )


def event_from_dict(data: JsonDict) -> Event:
    return Event(
        event_id=str(data["event_id"]),
        run_id=str(data["run_id"]),
        event_type=EventType(data["event_type"]),
        message=str(data.get("message", "")),
        created_at=str(data.get("created_at") or utc_now()),
        actor=str(data.get("actor", "system")),
        payload=dict(data.get("payload") or {}),
    )

