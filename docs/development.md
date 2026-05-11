# Local Development

## Bootstrap

```bash
uv sync --extra dev
uv run python scripts/check_import_boundaries.py
uv run --extra dev pytest
```

## Local Demo

Run the standalone mock execution path without ScheduleOS, graphify, or live model services:

```bash
uv run coi-demo --task examples/tasks/local_bootstrap.task.json --output-dir .coi-demo
```

The demo writes:

- `.coi-demo/task.json`
- `.coi-demo/artifacts/{run_id}/task-run.artifact.json`
- `.coi-demo/artifacts/{run_id}/execution-log.artifact.json`
- `.coi-demo/artifacts/{run_id}/result-bundle.artifact.json`
- `.coi-demo/summary.json`

## API

```bash
uv run coi-api --host 127.0.0.1 --port 8765 --storage-root .coi-api
```

Endpoints:

- `GET /health`
- `POST /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/summary`
- `POST /bootstrap`

## ScheduleOS Adapter

```bash
uv run coi-scheduleos examples/tasks/local_bootstrap.task.json --output-dir .coi-scheduleos
```

Only `repo.bootstrap` is supported in the first ScheduleOS-facing slice. Unsupported task types return a stable `unsupported` result instead of falling through to undefined behavior.

## Live Ollama Check

The default test suite uses the mock backend. To exercise the live Ollama adapter explicitly:

```bash
COI_RUN_LIVE_OLLAMA=1 uv run --extra dev pytest tests/test_orchestrator_api_integration.py::test_live_ollama_backend_availability_or_typed_failure
```

If Ollama is unavailable, the test reports a typed runtime failure path rather than treating local setup as a code regression.
