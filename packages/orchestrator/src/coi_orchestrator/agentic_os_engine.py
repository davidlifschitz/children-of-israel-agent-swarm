from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, TypedDict

from coi_contracts import RunStatus, WorkerRequest, new_id, to_jsonable, utc_now
from coi_runtime import MockRuntimeBackend, OllamaRuntimeBackend, RuntimeBackend
from coi_runtime.profiles import TierRuntimeProfile, load_tier_profiles

try:  # pragma: no cover - LangGraph is optional in the local deterministic path.
    from langgraph.graph import END, StateGraph  # type: ignore
except ImportError:  # pragma: no cover - exercised by default repo tests.
    END = "__end__"
    StateGraph = None

LANGGRAPH_AVAILABLE = StateGraph is not None


JsonDict = dict[str, Any]


@dataclass(slots=True)
class RunRequest:
    goal: str
    repo_path: str
    run_id: str = field(default_factory=lambda: new_id("agentic_os_run"))
    mode: str = "deterministic"
    branch: str | None = None
    approval_policy: dict[str, str] = field(default_factory=dict)
    approvals: list[JsonDict] = field(default_factory=list)
    artifacts: list[JsonDict] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
    requested_stages: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "RunRequest":
        goal = str(data.get("goal") or data.get("mandate") or "").strip()
        repo_path = str(
            data.get("repo_path")
            or data.get("repository_path")
            or data.get("target_repo")
            or data.get("targetRepo")
            or ""
        ).strip()
        if not goal:
            raise ValueError("RunRequest.goal is required")
        if not repo_path:
            raise ValueError("RunRequest.repo_path is required")
        return cls(
            goal=goal,
            repo_path=repo_path,
            run_id=str(data.get("run_id") or new_id("agentic_os_run")),
            mode=str(data.get("mode") or "deterministic"),
            branch=str(data["branch"]) if data.get("branch") else None,
            approval_policy=_approval_policy(data.get("approval_policy")),
            approvals=_json_list(data.get("approvals")),
            artifacts=_json_list(data.get("artifacts")),
            metadata=_mapping(data.get("metadata")),
            requested_stages=[str(stage) for stage in data.get("requested_stages") or []],
        )


@dataclass(slots=True)
class RunEvent:
    run_id: str
    type: str
    message: str
    stage: str | None = None
    status: str = "completed"
    actor: str = "system"
    tier: str | None = None
    model_policy: JsonDict = field(default_factory=dict)
    payload: JsonDict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: new_id("agentic_os_event"))
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(frozen=True, slots=True)
class RepoDeliveryStage:
    name: str
    tribe_id: str
    prompt: str


REPO_DELIVERY_STAGES: tuple[RepoDeliveryStage, ...] = (
    RepoDeliveryStage("intake", "moses", "Clarify the repo delivery mandate and constraints."),
    RepoDeliveryStage("spec", "judah", "Turn the mandate into a scoped implementation spec."),
    RepoDeliveryStage("plan", "joseph", "Produce the next concrete execution plan."),
    RepoDeliveryStage("implementation", "reuben", "Prepare implementation actions without pushing."),
    RepoDeliveryStage("verification", "benjamin", "Verify safety, trust, and test evidence."),
    RepoDeliveryStage("pr", "asher", "Prepare the final PR-ready summary and handoff."),
)


class _RepoDeliveryGraphState(TypedDict):
    events: list[RunEvent]
    pending_approvals: list[str]


class JethroRepoDeliveryEngine:
    def __init__(
        self,
        *,
        repo_root: str | Path,
        config_path: str | Path | None = None,
        backend: RuntimeBackend | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.config_path = Path(config_path) if config_path else self.repo_root / "config" / "mission.yaml"
        self.profiles = load_tier_profiles(self.config_path)
        self.backend = backend or _default_backend()

    def stream(self, request: RunRequest) -> Iterator[RunEvent]:
        stages = self._selected_stages(request)
        stage_names = [stage.name for stage in stages]
        use_langgraph = _langgraph_available()
        pending_approvals: list[str] = []
        yield self._event(
            request,
            event_type="run.started",
            message="Agentic OS repo delivery run started.",
            actor="moses",
            profile=self.profiles["moses"],
            payload={
                "repo_path": request.repo_path,
                "goal": request.goal,
                "mode": request.mode,
                "stages": stage_names,
                "langgraph_available": use_langgraph,
                "execution_path": "langgraph" if use_langgraph else "deterministic_fallback",
            },
        )
        failed = False
        if use_langgraph:
            stage_events, pending_approvals = self._run_langgraph(request, stages)
            failed = any(event.type == "run.failed" for event in stage_events)
            yield from stage_events
        else:
            fallback = self._event(
                request,
                event_type="runtime.fallback",
                message="LangGraph is not installed; using deterministic linear fallback.",
                actor="moses",
                profile=self.profiles["moses"],
                payload={
                    "concern": "langgraph_dependency_missing",
                    "dependency": "langgraph",
                    "install_extra": "langgraph",
                    "install_command": "uv sync --extra dev --extra langgraph",
                },
            )
            yield fallback
            stage_events = list(self._run_deterministic(request, stages, pending_approvals))
            failed = any(event.type == "run.failed" for event in stage_events)
            yield from stage_events

        yield self._event(
            request,
            event_type="run.result",
            message=(
                "Agentic OS repo delivery run failed."
                if failed
                else f"Agentic OS repo delivery run is waiting for {pending_approvals[0]} approval."
                if pending_approvals
                else "Agentic OS repo delivery run is ready for control-plane handling."
            ),
            actor="moses",
            profile=self.profiles["moses"],
            payload={
                "status": "failed" if failed else "waiting_approval" if pending_approvals else "ready_for_agentic_os",
                "run_status": RunStatus.FAILED.value
                if failed
                else "awaiting_approval"
                if pending_approvals
                else RunStatus.SUCCEEDED.value,
                "pending_approval_gates": pending_approvals,
                "stages": stage_names,
                "ready_actions": [
                    {
                        "type": "github.push_pr",
                        "status": "pending_approval",
                        "gate": "pr",
                    }
                ],
            },
        )

    def _run_deterministic(
        self,
        request: RunRequest,
        stages: list[RepoDeliveryStage],
        pending_approvals: list[str],
    ) -> Iterator[RunEvent]:
        for stage in stages:
            pending_count = len(pending_approvals)
            events = self._stage_events(request, stage, pending_approvals)
            yield from events
            if any(event.type == "run.failed" for event in events):
                break
            if len(pending_approvals) > pending_count:
                break

    def _run_langgraph(
        self,
        request: RunRequest,
        stages: list[RepoDeliveryStage],
    ) -> tuple[list[RunEvent], list[str]]:
        if not stages:
            return [], []
        graph = StateGraph(_RepoDeliveryGraphState)
        for stage in stages:
            graph.add_node(stage.name, self._langgraph_stage_node(request, stage))
        graph.set_entry_point(stages[0].name)
        for current, following in zip(stages, stages[1:], strict=False):
            graph.add_edge(current.name, following.name)
        graph.add_edge(stages[-1].name, END)
        compiled = graph.compile()
        state = compiled.invoke({"events": [], "pending_approvals": []})
        return list(state.get("events", [])), list(state.get("pending_approvals", []))

    def _langgraph_stage_node(self, request: RunRequest, stage: RepoDeliveryStage):
        def run_stage(state: _RepoDeliveryGraphState) -> _RepoDeliveryGraphState:
            events = list(state.get("events", []))
            pending_approvals = list(state.get("pending_approvals", []))
            if pending_approvals:
                return {"events": events, "pending_approvals": pending_approvals}
            events.extend(self._stage_events(request, stage, pending_approvals))
            return {"events": events, "pending_approvals": pending_approvals}

        return run_stage

    def _stage_events(
        self,
        request: RunRequest,
        stage: RepoDeliveryStage,
        pending_approvals: list[str],
    ) -> list[RunEvent]:
        events: list[RunEvent] = []
        if _approval_required(request, stage.name):
            pending_approvals.append(stage.name)
            events.append(
                self._event(
                    request,
                    event_type="approval.waiting",
                    message=f"Approval required before {stage.name}.",
                    stage=stage.name,
                    status="waiting_approval",
                    actor="moses",
                    profile=self.profiles["moses"],
                    payload={"gate": stage.name, "action": f"approve:{stage.name}"},
                )
            )
            return events

        profile = self.profiles[stage.tribe_id]
        worker_request = WorkerRequest(
            request_id=new_id("agentic_os_worker"),
            run_id=request.run_id,
            tribe_id=stage.tribe_id,
            tier=profile.tier,
            task_type=f"agentic_os.repo_delivery.{stage.name}",
            mandate=request.goal,
            prompt=stage.prompt,
            payload={
                "stage": stage.name,
                "repo_path": request.repo_path,
                "branch": request.branch,
                "metadata": request.metadata,
            },
            runtime_profile_id=profile.profile_id,
        )
        events.append(
            self._event(
                request,
                event_type="stage.started",
                message=f"{stage.name} stage started.",
                stage=stage.name,
                status="running",
                actor=stage.tribe_id,
                profile=profile,
            )
        )
        events.append(
            self._event(
                request,
                event_type="worker.dispatched",
                message=f"Dispatched {stage.tribe_id} for {stage.name}.",
                stage=stage.name,
                status="running",
                actor=stage.tribe_id,
                profile=profile,
                payload={"worker_request": to_jsonable(worker_request)},
            )
        )
        worker_result = self.backend.execute(worker_request)
        if worker_result.status != RunStatus.SUCCEEDED:
            failure = worker_result.failure
            events.append(
                self._event(
                    request,
                    event_type="run.failed",
                    message=failure.message if failure else f"{stage.name} stage failed.",
                    stage=stage.name,
                    status="failed",
                    actor=stage.tribe_id,
                    profile=profile,
                    payload={"worker_result": to_jsonable(worker_result)},
                )
            )
            return events
        stage_output = _stage_output(stage.name, worker_result.output)
        artifact = _write_stage_artifact(request, stage, worker_result.output, stage_output)
        events.append(
            self._event(
                request,
                event_type="stage.completed",
                message=f"{stage.name} stage completed.",
                stage=stage.name,
                actor=stage.tribe_id,
                profile=profile,
                payload={
                    "worker_result": to_jsonable(worker_result),
                    "output": stage_output,
                    "artifact": artifact,
                },
            )
        )
        return events

    def _selected_stages(self, request: RunRequest) -> list[RepoDeliveryStage]:
        if not request.requested_stages:
            return list(REPO_DELIVERY_STAGES)
        requested = set(request.requested_stages)
        unknown = sorted(requested - {stage.name for stage in REPO_DELIVERY_STAGES})
        if unknown:
            raise ValueError(f"Unknown requested stages: {', '.join(unknown)}")
        return [stage for stage in REPO_DELIVERY_STAGES if stage.name in requested]

    def _event(
        self,
        request: RunRequest,
        *,
        event_type: str,
        message: str,
        actor: str,
        profile: TierRuntimeProfile,
        stage: str | None = None,
        status: str = "completed",
        payload: JsonDict | None = None,
    ) -> RunEvent:
        return RunEvent(
            run_id=request.run_id,
            type=event_type,
            message=message,
            stage=stage,
            status=status,
            actor=actor,
            tier=profile.tier.value,
            model_policy=_model_policy(profile),
            payload=payload or {},
        )


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _langgraph_available() -> bool:
    return LANGGRAPH_AVAILABLE and StateGraph is not None


def _model_policy(profile: TierRuntimeProfile) -> JsonDict:
    return {
        "profile_id": profile.profile_id,
        "tribe_id": profile.tribe_id,
        "tier": profile.tier.value,
        "model_class": profile.model_class,
        "provider": profile.provider,
        "model": profile.model,
        "json_mode": profile.json_mode,
        "timeout_seconds": profile.timeout_seconds,
        "options": profile.options or {},
    }


def _approval_required(request: RunRequest, stage: str) -> bool:
    if stage in _approved_stages(request):
        return False
    return request.approval_policy.get(stage, "").lower() in {"required", "true", "yes"}


def _approved_stages(request: RunRequest) -> set[str]:
    approved: set[str] = set()
    for approval in request.approvals:
        stage = str(approval.get("stage") or "")
        status = str(approval.get("status") or "")
        if stage and status.lower() == "approved":
            approved.add(stage)
    return approved


def _stage_output(stage: str, worker_output: JsonDict) -> JsonDict:
    return {
        "stage": stage,
        "summary": worker_output.get("summary", f"Deterministic {stage} output."),
        "artifact_status": "ready",
    }


def _mapping(value: Any) -> JsonDict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return dict(value)


def _json_list(value: Any) -> list[JsonDict]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Expected a JSON array")
    return [_mapping(item) for item in value]


def _string_mapping(value: Any) -> dict[str, str]:
    return {str(key): str(item) for key, item in _mapping(value).items()}


def _approval_policy(value: Any) -> dict[str, str]:
    raw = _mapping(value)
    policy = {
        str(key): str(item)
        for key, item in raw.items()
        if key not in {"required_stages", "requiredStages"}
    }
    required_stages = raw.get("required_stages") or raw.get("requiredStages") or []
    if isinstance(required_stages, str):
        required_stages = [required_stages]
    if not isinstance(required_stages, list):
        raise ValueError("approval_policy.required_stages must be a list")
    for stage in required_stages:
        policy[str(stage)] = "required"
    return policy


def _default_backend() -> RuntimeBackend:
    backend_name = os.environ.get("AGENTIC_OS_COI_BACKEND", "auto").strip().lower()
    model = os.environ.get("AGENTIC_OS_OLLAMA_MODEL") or os.environ.get("OLLAMA_MODEL") or "qwen2.5-coder:1.5b"
    ollama = OllamaRuntimeBackend(model=model)
    if backend_name == "mock":
        return MockRuntimeBackend(name="agentic-os-mock")
    if backend_name == "ollama":
        return ollama
    if ollama.available():
        return ollama
    return MockRuntimeBackend(name="agentic-os-mock-fallback")


def _write_stage_artifact(
    request: RunRequest,
    stage: RepoDeliveryStage,
    worker_output: JsonDict,
    stage_output: JsonDict,
) -> JsonDict:
    repo_path = Path(request.repo_path).expanduser().resolve()
    artifact_dir = repo_path / ".agentic-os" / "runs" / request.run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{stage.name}.md"
    artifact_path.write_text(
        "\n".join(
            [
                f"# {stage.name.title()} Output",
                "",
                f"- run: `{request.run_id}`",
                f"- stage: `{stage.name}`",
                f"- actor: `{stage.tribe_id}`",
                f"- backend: `{getattr(worker_output, 'name', 'runtime')}`",
                "",
                "## Goal",
                "",
                request.goal,
                "",
                "## Summary",
                "",
                str(stage_output.get("summary") or ""),
                "",
                "## Worker Output",
                "",
                "```json",
                json.dumps(worker_output, indent=2, sort_keys=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "path": str(artifact_path),
        "relative_path": str(artifact_path.relative_to(repo_path)),
        "content_type": "text/markdown",
    }
