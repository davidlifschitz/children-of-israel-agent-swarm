"""test_oral_law.py — Tests for the OralLawEngine and PrecedentStore."""
import pytest
import time
from pathlib import Path
from unittest.mock import patch

from children_of_israel.oral_law_engine import OralLawEngine
from children_of_israel.precedent_store import PrecedentStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state():
    """Return a minimal AgentState-compatible dict."""
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


# ---------------------------------------------------------------------------
# OL-001: Context Over Code
# ---------------------------------------------------------------------------

def test_ol001_context_over_code_valid_judge():
    """A Tier 1 judge (dan) may suspend a directive; returns True and logs OL-001."""
    engine = OralLawEngine()
    state = _make_state()
    result = engine.apply_context_over_code(state, "P-IV-001", "dan")
    assert result is True
    assert any("OL-001" in v for v in state["constitution_violations"]), (
        "Expected an OL-001 note in constitution_violations"
    )


def test_ol001_context_over_code_invalid_judge():
    """A non-Tier-1 tribe (reuben) cannot suspend a directive; returns False."""
    engine = OralLawEngine()
    state = _make_state()
    result = engine.apply_context_over_code(state, "P-IV-001", "reuben")
    assert result is False


# ---------------------------------------------------------------------------
# OL-002: The Dan Precedent
# ---------------------------------------------------------------------------

def test_ol002_log_precedent_returns_id(tmp_path):
    """log_precedent returns a precedent ID starting with 'DAN-TEST_CONFLICT-'."""
    engine = OralLawEngine()
    state = _make_state()
    store_path = tmp_path / "data" / "precedents.jsonl"
    store_path.parent.mkdir(parents=True, exist_ok=True)

    with patch.object(PrecedentStore, "__init__", lambda self: None), \
         patch.object(PrecedentStore, "write", return_value=None), \
         patch.object(PrecedentStore, "_ensure_dir", return_value=None):
        precedent_id = engine.log_precedent(state, "test_conflict", "Test ruling")

    assert precedent_id.startswith("DAN-TEST_CONFLICT-"), (
        f"Unexpected precedent ID format: {precedent_id}"
    )


def test_ol002_log_precedent_updates_state(tmp_path):
    """log_precedent appends the precedent ID to state['oral_law_precedents']."""
    engine = OralLawEngine()
    state = _make_state()

    with patch.object(PrecedentStore, "__init__", lambda self: None), \
         patch.object(PrecedentStore, "write", return_value=None), \
         patch.object(PrecedentStore, "_ensure_dir", return_value=None):
        precedent_id = engine.log_precedent(state, "test_conflict", "Test ruling")

    assert len(state["oral_law_precedents"]) == 1
    assert state["oral_law_precedents"][0] == precedent_id


# ---------------------------------------------------------------------------
# OL-003: Proportional Escalation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("impact,expected_tribe", [
    ("minor",            "issachar"),
    ("major",            "dan"),
    ("critical",         "judah"),
    ("unknown_impact",   "dan"),
])
def test_ol003_proportional_escalation(impact, expected_tribe):
    """resolve_proportional_escalation returns the correct tribe for each impact level."""
    engine = OralLawEngine()
    state = _make_state()
    result = engine.resolve_proportional_escalation(state, impact)
    assert result == expected_tribe, (
        f"Impact '{impact}': expected '{expected_tribe}', got '{result}'"
    )


# ---------------------------------------------------------------------------
# OL-004: The Silence of Moses
# ---------------------------------------------------------------------------

def test_ol004_sla_not_exceeded():
    """When elapsed < 300 s the action must be 'await'."""
    engine = OralLawEngine()
    state = _make_state()
    result = engine.apply_moses_silence_fallback(state, 100.0)
    assert result["action"] == "await", (
        f"Expected 'await' for 100 s, got {result['action']!r}"
    )


def test_ol004_sla_exceeded():
    """When elapsed > 300 s the action must be 'conservative_hold' deferred to levi."""
    engine = OralLawEngine()
    state = _make_state()
    result = engine.apply_moses_silence_fallback(state, 400.0)
    assert result["action"] == "conservative_hold", (
        f"Expected 'conservative_hold' for 400 s, got {result['action']!r}"
    )
    assert result["defer_to"] == "levi", (
        f"Expected defer_to='levi', got {result.get('defer_to')!r}"
    )
