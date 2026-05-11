from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coi_contracts import (
    CheckpointRecord,
    Event,
    EventType,
    LawVerdict,
    LawVerdictKind,
    PrecedentRecord,
    Run,
    RunStatus,
    Tier,
    WorkerRequest,
    new_id,
    to_jsonable,
    utc_now,
)
from coi_law_engine import LawEngine, LawRegistry
from coi_runtime import HermesRuntimeAdapter, MockRuntimeBackend, OllamaRuntimeBackend, RuntimeBackend
from coi_runtime.profiles import TRIBE_TIERS, load_tier_profiles
from coi_storage import FileStorage, InMemoryStorage


HERMES_ELIGIBLE = {"reuben", "naphtali", "asher"}


@dataclass(slots=True)
class SwarmOrchestrator:
    storage: Any
    law_engine: LawEngine
    backend: RuntimeBackend
    hermes_backend: RuntimeBackend | None = None
    profiles: dict[str, Any] | None = None

    def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        run = self._create_run(task)
        self._event(run.run_id, EventType.RUN_CREATED, "Run created.", payload={"task_type": run.task_type})
        task_verdicts = self.law_engine.evaluate_task(run.run_id, task)
        self._record_verdicts(task_verdicts)
        if any(verdict.blocks_execution for verdict in task_verdicts):
            run.status = RunStatus.BLOCKED
            run.updated_at = utc_now()
            self._event(run.run_id, EventType.RUN_FAILED, "Run blocked by law engine.", actor="simeon")
            run.summary = self._summary(run, task_verdicts, [], {"blocked": True})
            self.storage.update(run)
            return run.summary

        run.status = RunStatus.RUNNING
        run.updated_at = utc_now()
        self.storage.update(run)
        self._event(run.run_id, EventType.RUN_STARTED, "Run started.", actor="judah")

        worker_request = self._worker_request(run, task)
        self._event(
            run.run_id,
            EventType.WORKER_DISPATCHED,
            f"Dispatched to {worker_request.tribe_id}.",
            actor="judah",
            payload={"tier": worker_request.tier.value},
        )

        result = self._execute_worker(worker_request)
        self._event(
            run.run_id,
            EventType.WORKER_COMPLETED,
            f"Worker {result.worker_id} completed with {result.status}.",
            actor=result.worker_id,
            payload={"output": result.output, "failure": to_jsonable(result.failure)},
        )
        result_verdicts = self.law_engine.evaluate_worker_result(result)
        self._record_verdicts(result_verdicts)

        self._event(run.run_id, EventType.LAW_VERDICT, "Compliance stage completed.", actor="simeon")
        checkpoint = CheckpointRecord(
            checkpoint_id=new_id("checkpoint"),
            run_id=run.run_id,
            stage="memory",
            state={"worker_output": result.output, "status": result.status.value},
        )
        self.storage.save(checkpoint)
        self._event(run.run_id, EventType.CHECKPOINT_SAVED, "Memory checkpoint saved.", actor="levi")

        blocked = any(verdict.blocks_execution for verdict in result_verdicts)
        run.status = RunStatus.BLOCKED if blocked else result.status
        if result.status == RunStatus.FAILED and not blocked:
            run.status = RunStatus.FAILED
        terminal = EventType.RUN_FAILED if run.status in {RunStatus.FAILED, RunStatus.BLOCKED} else EventType.RUN_SUCCEEDED
        self._event(run.run_id, terminal, f"Run terminal status: {run.status}.", actor="judah")
        run.summary = self._summary(run, task_verdicts + result_verdicts, [to_jsonable(result)], {"blocked": blocked})
        run.updated_at = utc_now()
        self.storage.update(run)
        return run.summary

    def get_run(self, run_id: str) -> Run | None:
        return self.storage.get(run_id)

    def get_events(self, run_id: str) -> list[Event]:
        return self.storage.list_by_run(run_id)

    def get_summary(self, run_id: str) -> dict[str, Any] | None:
        run = self.storage.get(run_id)
        return run.summary if run else None

    def _create_run(self, task: dict[str, Any]) -> Run:
        task_type = str(task.get("task_type") or task.get("type") or "unknown")
        mandate = str(task.get("mandate") or "")
        metadata = {
            "source": task.get("source") or "local",
            "external_id": task.get("id"),
            "optional_integrations": task.get("optional_integrations") or {},
        }
        run = Run(run_id=new_id("run"), task_type=task_type, mandate=mandate, metadata=metadata)
        return self.storage.create(run)

    def _worker_request(self, run: Run, task: dict[str, Any]) -> WorkerRequest:
        tribe_id = _route_task(run.task_type)
        tier = TRIBE_TIERS.get(tribe_id, Tier.TIER_4)
        profile = (self.profiles or {}).get(tribe_id)
        return WorkerRequest(
            request_id=new_id("worker"),
            run_id=run.run_id,
            tribe_id=tribe_id,
            tier=tier,
            task_type=run.task_type,
            mandate=run.mandate,
            prompt=str(task.get("prompt") or run.mandate),
            payload=_mapping_payload(task.get("payload")),
            runtime_profile_id=profile.profile_id if profile else None,
        )

    def _execute_worker(self, worker_request: WorkerRequest):
        if worker_request.tribe_id in HERMES_ELIGIBLE and self.hermes_backend is not None:
            hermes_result = self.hermes_backend.execute(worker_request)
            if hermes_result.status == RunStatus.SUCCEEDED:
                return hermes_result
            self._event(
                worker_request.run_id,
                EventType.FALLBACK,
                "Hermes branch unavailable or failed; returning to tribal backend.",
                actor="gad",
                payload={"failure": to_jsonable(hermes_result.failure)},
            )
        return self.backend.execute(worker_request)

    def _record_verdicts(self, verdicts: list[LawVerdict]) -> None:
        for verdict in verdicts:
            self._event(
                verdict.run_id,
                EventType.LAW_VERDICT,
                verdict.message,
                actor="simeon",
                payload={"verdict": to_jsonable(verdict)},
            )
            if verdict.kind in {LawVerdictKind.HARD_BLOCK, LawVerdictKind.ADVISORY}:
                precedent = PrecedentRecord(
                    precedent_id=new_id("precedent"),
                    run_id=verdict.run_id,
                    verdict_id=verdict.verdict_id,
                    rule_id=verdict.rule_id,
                    ruling=verdict.message,
                )
                self.storage.save(precedent)
                self._event(
                    verdict.run_id,
                    EventType.PRECEDENT_RECORDED,
                    f"Recorded precedent for {verdict.rule_id}.",
                    actor="dan",
                    payload={"precedent": to_jsonable(precedent)},
                )

    def _event(
        self,
        run_id: str,
        event_type: EventType,
        message: str,
        actor: str = "system",
        payload: dict[str, Any] | None = None,
    ) -> Event:
        return self.storage.append(
            Event(
                event_id=new_id("event"),
                run_id=run_id,
                event_type=event_type,
                message=message,
                actor=actor,
                payload=payload or {},
            )
        )

    def _summary(
        self,
        run: Run,
        verdicts: list[LawVerdict],
        worker_results: list[dict[str, Any]],
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        events = self.storage.list_by_run(run.run_id)
        artifact_refs = [
            f"artifacts/{run.run_id}/task-run.artifact.json",
            f"artifacts/{run.run_id}/execution-log.artifact.json",
            f"artifacts/{run.run_id}/result-bundle.artifact.json",
        ]
        return {
            "run_id": run.run_id,
            "task_type": run.task_type,
            "status": run.status.value,
            "summary": _human_summary(run, worker_results, verdicts),
            "artifact_refs": artifact_refs,
            "event_count": len(events),
            "law_verdicts": [to_jsonable(verdict) for verdict in verdicts],
            "worker_results": worker_results,
            **extra,
        }


def build_local_orchestrator(
    repo_root: str | Path,
    storage_root: str | Path | None = None,
    backend: RuntimeBackend | None = None,
    use_hermes: bool = False,
) -> SwarmOrchestrator:
    root = Path(repo_root)
    registry = LawRegistry.from_repo_root(root)
    profiles = load_tier_profiles(root / "config" / "mission.yaml")
    storage = FileStorage(storage_root) if storage_root else InMemoryStorage()
    primary_backend = backend or MockRuntimeBackend()
    hermes = HermesRuntimeAdapter() if use_hermes else None
    return SwarmOrchestrator(
        storage=storage,
        law_engine=LawEngine(registry),
        backend=primary_backend,
        hermes_backend=hermes,
        profiles=profiles,
    )


def build_ollama_orchestrator(repo_root: str | Path, storage_root: str | Path | None = None) -> SwarmOrchestrator:
    root = Path(repo_root)
    return build_local_orchestrator(
        repo_root=root,
        storage_root=storage_root,
        backend=OllamaRuntimeBackend(),
        use_hermes=False,
    )


def _route_task(task_type: str) -> str:
    if task_type.startswith("repo.bootstrap"):
        return "reuben"
    if task_type.startswith("research."):
        return "issachar"
    if task_type.startswith("publish."):
        return "asher"
    if task_type.startswith("security."):
        return "benjamin"
    return "judah"


def _human_summary(run: Run, worker_results: list[dict[str, Any]], verdicts: list[LawVerdict]) -> str:
    blockers = [verdict for verdict in verdicts if verdict.blocks_execution]
    if blockers:
        return f"{run.task_type} blocked by {blockers[0].rule_id}: {blockers[0].message}"
    if worker_results:
        output = worker_results[-1].get("output") or {}
        if isinstance(output, dict) and output.get("summary"):
            return str(output["summary"])
    return f"{run.task_type} finished with status {run.status.value}."


def _mapping_payload(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
