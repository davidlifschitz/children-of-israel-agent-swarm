.PHONY: install install-dev install-hermes run test

install:
	uv sync

install-dev:
	uv sync --extra dev

install-hermes:
	@echo "Installing Hermes Agent (Nous Research)..."
	@echo "Note: Requires Linux, macOS, or WSL2. Native Windows is not supported."
	curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

run:
	uv run python run_swarm.py

test:
	uv run pytest tests/

test-verbose:
	uv run pytest tests/ -v
