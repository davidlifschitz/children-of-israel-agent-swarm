"""conftest.py — shared pytest fixtures for Children of Israel Agent Swarm tests."""
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile, shutil


@pytest.fixture
def mock_llm_call():
    """Patch children_of_israel.llm.llm_call to return a predictable mock dict."""
    with patch(
        "children_of_israel.llm.llm_call",
        return_value={"result": "mock output", "mandate": "test mandate", "output": "mock"},
    ) as mock:
        yield mock


@pytest.fixture
def minimal_state():
    """Return a minimal AgentState-compatible dict with all required fields."""
    return {
        "mission": "Test mission",
        "mandate": "Test mandate",
        "task": "Test task",
        "jethro_tier": 4,
        "session_id": "test-session-001",
        "constitution_violations": [],
        "oral_law_precedents": [],
        "current_tribe": "reuben",
        "escalate": False,
        "escalation_reason": "",
    }


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temp directory and yield its path. No patching needed — callers
    use monkeypatch or direct attribute overrides to redirect file I/O."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir
