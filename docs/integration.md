# Delegated bootstrap integration

## Purpose

This repo proves that the swarm can accept a shared task, validate it, delegate execution to `spec-to-repo`, and emit standard execution-layer artifacts.

## Runnable demo

```bash
uv run python scripts/run_e2e_demo.py --agentic-os ../agentic-os --spec-to-repo ../spec-to-repo
```

## Flow

1. load `agentic-os/examples/tasks/bootstrap-spec-to-repo.task.json`
2. validate the shared task shape
3. delegate the bootstrap task to `spec-to-repo`
4. emit `task-run`, `execution-log`, and `result-bundle` artifacts
5. hand the emitted artifacts to `graphify` for registration and query

## Output layout

- `task.json`
- `spec-to-repo-output/`
- `artifacts/task-run.artifact.json`
- `artifacts/execution-log.artifact.json`
- `artifacts/result-bundle.artifact.json`
- `summary.json`
