# Foundations Runtime Closure Design

## Active Goal

Close the open foundations and integration issue queue by landing a minimal executable local swarm layer that still treats the existing skills, law, and docs as the product source of truth.

## Design

The repository remains a skills and governance pack, but gains a small Python execution layer under `packages/`. The layer is deliberately contract-first:

- `coi_contracts` owns run lifecycle, worker, event, law verdict, and storage repository contracts.
- `coi_runtime` owns backend adapters for mock execution, Ollama, Hermes, and tier runtime profiles.
- `coi_law_engine` loads `law/` and `config/` YAML artifacts and returns typed hard-block or advisory verdicts.
- `coi_storage` provides in-memory repositories for tests and JSON/JSONL file repositories for local durability.
- `coi_orchestrator` owns route selection, lifecycle transitions, compliance checks, memory checkpoints, fallback events, and summaries.
- `coi_api` exposes a small stdlib HTTP control plane for health, create-run, get-run, events, summaries, and bootstrap.
- `coi_integrations` exposes the thin ScheduleOS-facing adapter and shell result shape.

## Runtime Semantics

V1 execution is synchronous and local. A task is validated, turned into a run, dispatched to a tier-selected worker request, checked by the law engine, written to storage, and summarized. Hermes is modeled as an optional branch for eligible tribes. If Hermes is unavailable, the orchestrator emits an explicit fallback event and uses the configured normal backend; the documentation must describe that exact behavior.

## Scope Boundaries

This slice does not build a distributed engine, web console, real queue, or autonomous cloud deployment. Ollama is opt-in and skipped when unavailable. File storage is enough for durable local runs and API inspection; database storage remains a later extension.

## Acceptance Mapping

- Issues #8-#13: packages, contracts, CI, and boundaries.
- Issues #14-#21: runtime/orchestrator execution and Hermes alignment.
- Issues #22-#27: executable law and storage.
- Issues #28-#30: API control plane.
- Issues #31-#34 and #4-#7: local demo, live opt-in path, docs, ScheduleOS adapter, and validation.

