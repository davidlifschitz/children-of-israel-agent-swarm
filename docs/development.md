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

## Agentic OS Runtime Routing

Agentic OS repo-delivery runs use profile routing by default:

- Moses/root intake uses the `openrouter_reasoning` model class.
- Lower Jethro tiers keep the local Ollama classes from `config/mission.yaml`.
- If `OPENROUTER_API_KEY` is not set, the OpenRouter profile falls back to mock output with explicit runtime metadata.

Live OpenRouter usage:

```bash
export OPENROUTER_API_KEY="..."
export AGENTIC_OS_COI_BACKEND=profile
export AGENTIC_OS_OPENROUTER_MODEL="openrouter/auto"
```

Force one backend when debugging:

```bash
AGENTIC_OS_COI_BACKEND=mock .venv/bin/python -m pytest -q tests/test_agentic_os_runner.py
AGENTIC_OS_COI_BACKEND=ollama .venv/bin/python -m pytest -q tests/test_agentic_os_runner.py
AGENTIC_OS_COI_BACKEND=openrouter OPENROUTER_API_KEY="..." .venv/bin/python -m coi_api.agentic_os_runner --request /path/to/request.json
```
