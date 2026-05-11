from pathlib import Path

from coi_contracts import (
    CheckpointRecord,
    Event,
    EventType,
    PrecedentRecord,
    Run,
    RunStatus,
    WorkerResult,
    new_id,
)
from coi_law_engine import LawEngine, LawRegistry
from coi_storage import FileStorage, InMemoryStorage


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_law_registry_loads_all_artifacts():
    registry = LawRegistry.from_repo_root(REPO_ROOT)

    assert len(registry.hard_commandments) == 10
    assert registry.directive_count >= 600
    assert {"OL-001", "OL-002", "OL-003", "OL-004"} <= registry.oral_rule_ids


def test_law_engine_blocks_missing_mandate_and_warns_missing_source():
    engine = LawEngine(LawRegistry.from_repo_root(REPO_ROOT))
    verdicts = engine.evaluate_task("run_1", {"task_type": "repo.bootstrap"})

    assert any(verdict.blocks_execution for verdict in verdicts)
    assert any(verdict.rule_id == "P-IV-002" for verdict in verdicts)


def test_law_engine_warns_on_empty_worker_output():
    engine = LawEngine(LawRegistry.from_repo_root(REPO_ROOT))
    verdicts = engine.evaluate_worker_result(
        WorkerResult("worker_1", "run_1", "reuben:mock", RunStatus.SUCCEEDED, output={})
    )

    assert any(verdict.rule_id == "P-UH-005" for verdict in verdicts)
    assert not any(verdict.kind == "pass" for verdict in verdicts)


def test_file_storage_persists_runs_events_checkpoints_and_precedents(tmp_path):
    storage = FileStorage(tmp_path)
    run = storage.create(Run(run_id="run_1", task_type="repo.bootstrap", mandate="demo"))
    event = storage.append(Event(new_id("event"), run.run_id, EventType.RUN_CREATED, "created"))
    checkpoint = storage.save(CheckpointRecord(new_id("checkpoint"), run.run_id, "memory", {"ok": True}))
    precedent = storage.save(PrecedentRecord(new_id("precedent"), run.run_id, "verdict_1", "C3", "blocked"))

    reloaded = FileStorage(tmp_path)
    assert reloaded.get(run.run_id).task_type == "repo.bootstrap"
    assert reloaded.list_by_run(run.run_id)[0].event_id == event.event_id
    assert reloaded.get_latest(run.run_id).checkpoint_id == checkpoint.checkpoint_id
    assert reloaded.list_by_rule("C3")[0].precedent_id == precedent.precedent_id


def test_in_memory_storage_supports_local_development():
    storage = InMemoryStorage()
    run = storage.create(Run(run_id="run_2", task_type="repo.bootstrap", mandate="demo"))
    storage.append(Event(new_id("event"), run.run_id, EventType.RUN_CREATED, "created"))

    assert storage.get("run_2") == run
    assert len(storage.list_by_run("run_2")) == 1
