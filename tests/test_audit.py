"""test_audit.py — Tests for Simeon audit output and Levi audit log."""
import json
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from children_of_israel.tribes.tribe_levi import levi_node
from children_of_israel.tribes.tribe_simeon import simeon_node


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


_LEVI_MOCK_RESULT = {
    "tribe": "levi",
    "output_type": "memory_record",
    "records": ["record 1"],
    "gaps": [],
    "integrity_status": "ok",
    "escalate": False,
}

_SIMEON_FIRST_RESULT = {
    "tribe": "simeon",
    "output_type": "compliance_audit",
    "passed": True,
    "violations": [],
    "warnings": [],
    "ruling": "pass",
    "escalate": False,
}

_SIMEON_AUDIT_RESULT = {
    "violations_found": [],
    "severity": "low",
    "recommended_action": "Continue",
}


# ---------------------------------------------------------------------------
# Helper: build a fake Path.open context manager that captures writes
# ---------------------------------------------------------------------------

def _make_capturing_path_open(written_lines: list):
    """Return a drop-in replacement for Path.open that captures written lines."""
    real_path_open = Path.open  # keep a reference to the real method

    def fake_path_open(self, mode="r", **kwargs):
        if "a" in mode and "audit_log.jsonl" in str(self):
            buf = io.StringIO()

            class _CM:
                def __enter__(inner_self):
                    return buf

                def __exit__(inner_self, *a):
                    value = buf.getvalue()
                    if value:
                        written_lines.append(value)

            return _CM()
        # Fall back to real open for every other path
        return real_path_open(self, mode, **kwargs)

    return fake_path_open


# ---------------------------------------------------------------------------
# Levi audit log tests
# ---------------------------------------------------------------------------

def test_levi_creates_audit_log():
    """levi_node writes exactly one line to the audit log on first call."""
    written_lines = []

    with patch("children_of_israel.tribes.tribe_levi.llm_call", return_value=_LEVI_MOCK_RESULT), \
         patch.object(Path, "open", _make_capturing_path_open(written_lines)), \
         patch.object(Path, "mkdir", return_value=None), \
         patch.object(Path, "touch", return_value=None):
        levi_node(_make_state())

    assert len(written_lines) == 1, (
        f"Expected 1 audit line written, got {len(written_lines)}"
    )


def test_levi_audit_log_is_append_only():
    """levi_node appends one line per call; two calls produce two lines."""
    written_lines = []

    with patch("children_of_israel.tribes.tribe_levi.llm_call", return_value=_LEVI_MOCK_RESULT), \
         patch.object(Path, "open", _make_capturing_path_open(written_lines)), \
         patch.object(Path, "mkdir", return_value=None), \
         patch.object(Path, "touch", return_value=None):
        levi_node(_make_state())
        levi_node(_make_state())

    assert len(written_lines) == 2, (
        f"Expected 2 audit lines after two calls, got {len(written_lines)}"
    )


def test_levi_audit_record_has_required_keys():
    """Each audit record written by levi_node must contain the required keys."""
    written_lines = []

    with patch("children_of_israel.tribes.tribe_levi.llm_call", return_value=_LEVI_MOCK_RESULT), \
         patch.object(Path, "open", _make_capturing_path_open(written_lines)), \
         patch.object(Path, "mkdir", return_value=None), \
         patch.object(Path, "touch", return_value=None):
        levi_node(_make_state())

    assert len(written_lines) == 1, "No audit line was written"

    # The write call is json.dumps(record) + "\n"; strip the trailing newline
    raw = written_lines[0].rstrip("\n")
    record = json.loads(raw)

    required_keys = {
        "timestamp",
        "session_id",
        "mission",
        "constitution_violations",
        "oral_law_precedents",
    }
    missing = required_keys - set(record.keys())
    assert not missing, f"Audit record is missing keys: {missing}"


# ---------------------------------------------------------------------------
# Simeon compliance audit tests
# ---------------------------------------------------------------------------

def test_simeon_output_has_compliance_keys():
    """simeon_node returns a state whose tribe_output contains 'violations_found'."""
    # First llm_call = initial Simeon response, second = compliance audit result
    call_results = [_SIMEON_FIRST_RESULT, _SIMEON_AUDIT_RESULT]
    call_iter = iter(call_results)

    def mock_llm(*args, **kwargs):
        try:
            return next(call_iter)
        except StopIteration:
            return _SIMEON_AUDIT_RESULT

    with patch("children_of_israel.tribes.tribe_simeon.llm_call", side_effect=mock_llm):
        result_state = simeon_node(_make_state())

    tribe_output = result_state.get("tribe_output") or result_state.get("output") or {}
    assert isinstance(tribe_output, dict), (
        f"Expected tribe_output to be a dict, got {type(tribe_output)}"
    )
    assert "violations_found" in tribe_output, (
        f"tribe_output missing 'violations_found' key; keys present: {list(tribe_output.keys())}"
    )
