# Delegated bootstrap integration

## Purpose

This repo proves that the swarm can accept a shared task, validate it, delegate execution to `spec-to-repo`, and emit standard execution-layer artifacts.

## Runnable demo

```bash
uv run coi-demo --task examples/tasks/local_bootstrap.task.json --output-dir .coi-demo
```

## Flow

1. load `examples/tasks/local_bootstrap.task.json`
2. validate the task shape and mandate through the law engine
3. route the bootstrap task through the local orchestrator
4. execute with the mock runtime unless a caller explicitly selects a live backend
5. emit `task-run`, `execution-log`, and `result-bundle` artifacts
6. return a shell-facing summary that ScheduleOS can render

## Output layout

- `task.json`
- `spec-to-repo-output/`
- `artifacts/{run_id}/task-run.artifact.json`
- `artifacts/{run_id}/execution-log.artifact.json`
- `artifacts/{run_id}/result-bundle.artifact.json`
- `summary.json`

## ScheduleOS adapter

```bash
uv run coi-scheduleos examples/tasks/local_bootstrap.task.json --output-dir .coi-scheduleos
```

The first adapter intentionally supports only `repo.bootstrap`. Unsupported task types return a stable `unsupported` result so ScheduleOS does not need internal swarm knowledge to render the outcome.
