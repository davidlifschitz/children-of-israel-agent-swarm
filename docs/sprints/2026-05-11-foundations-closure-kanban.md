# Foundations Closure Kanban

Date: 2026-05-11

## Goal

Close the full open issue queue by landing one coherent foundations slice that turns the skills/playbook repo into a locally runnable execution layer without discarding the skills-first architecture.

## Kanban

| Lane | Issues | Outcome |
| --- | --- | --- |
| Standalone and ScheduleOS intake | #34, #4, #5, #6, #7 | Local mock task execution, ScheduleOS-facing adapter, stable shell summary, adapter validation |
| Bootstrap contracts | #8, #9, #10, #11, #12, #13 | Monorepo package skeleton, CI, import boundaries, lifecycle/worker/event/law/storage contracts |
| Runtime and orchestrator | #14, #15, #16, #17, #18, #19, #20, #21 | Backend interface, mock/Ollama/Hermes adapters, tier profiles, lifecycle routing, compliance and memory stages, documented Hermes semantics |
| Law and storage | #22, #23, #24, #25, #26, #27 | YAML artifact loader, hard-block/advisory verdicts, in-memory and durable repositories |
| API and quality | #28, #29, #30, #31, #32, #33 | Health/run/event/summary endpoints, mocked golden path, opt-in live runtime test path, developer bootstrap and migration docs |

## Dependency Order

1. Package and contract skeleton: #8 through #13.
2. Runtime and orchestrator against contracts: #14 through #21.
3. Law and storage behind interfaces: #22 through #27.
4. API and integration adapters over orchestrator/storage: #4 through #7 and #28 through #30.
5. Local demo, tests, CI, and docs: #31 through #34.

## Done Criteria

- `uv run --extra dev pytest` passes.
- Import-boundary validation passes.
- `uv run coi-demo --task examples/tasks/local_bootstrap.task.json --output-dir .coi-demo` emits local artifacts and a readable summary.
- `uv run coi-api --help` starts through the packaged CLI path.
- The branch is published through the `no-mistakes` gate when available.
- All 31 currently open issues are closed with a reference to the landed implementation.
