# Foundations Runtime Closure Implementation Plan

## Steps

1. Add top-level Python packaging and package directories for contracts, runtime, orchestrator, law engine, storage, API, and integrations.
2. Implement dataclass contracts with JSON helpers and protocol interfaces.
3. Implement runtime backends: deterministic mock, Ollama HTTP adapter with availability checks, Hermes CLI adapter with typed unavailable failures, and tier profiles loaded from `config/mission.yaml`.
4. Implement law artifact loading and simple hard-block/advisory evaluations grounded in the existing YAML.
5. Implement in-memory and file-backed repositories for runs, events, checkpoints, and precedents.
6. Implement the orchestrator as the lifecycle owner: create run, execute worker, law checks, fallback events, compliance and memory stages, summary.
7. Implement the stdlib HTTP API and ScheduleOS adapter.
8. Add local demo task, CLI scripts, tests, CI workflow, import-boundary checker, and developer docs.
9. Run focused and full verification, publish through `no-mistakes`, merge, then close all mapped issues.

## Verification

- `uv run python scripts/check_import_boundaries.py`
- `uv run --extra dev pytest`
- `uv run coi-demo --task examples/tasks/local_bootstrap.task.json --output-dir .coi-demo`
- `uv run coi-api --help`
