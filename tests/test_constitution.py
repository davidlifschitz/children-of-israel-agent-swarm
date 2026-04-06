"""test_constitution.py — Tests for ConstitutionEnforcer."""
import pytest
from children_of_israel.constitution_enforcer import ConstitutionEnforcer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _good_state():
    return {
        "mandate": "test",
        "jethro_tier": 4,
        "task": "summarize",
        "constitution_violations": [],
    }


def _good_output():
    return {"result": "good output", "status": "ok"}


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def test_enforcer_loads_constitution():
    """ConstitutionEnforcer initialises without error and loads 10 commandments."""
    enforcer = ConstitutionEnforcer()
    assert len(enforcer.commandments) == 10, (
        f"Expected 10 commandments, got {len(enforcer.commandments)}"
    )


# ---------------------------------------------------------------------------
# Pre-execution: check_pre_execution
# ---------------------------------------------------------------------------

def test_c3_missing_mandate():
    """Missing mandate key triggers a C3 violation."""
    enforcer = ConstitutionEnforcer()
    state = {"jethro_tier": 4, "task": "summarize", "constitution_violations": []}
    violations = enforcer.check_pre_execution(state)
    assert any("C3" in v for v in violations), f"No C3 violation found: {violations}"


def test_c3_empty_mandate():
    """An empty mandate string triggers a C3 violation."""
    enforcer = ConstitutionEnforcer()
    state = {"mandate": "", "jethro_tier": 4, "task": "summarize", "constitution_violations": []}
    violations = enforcer.check_pre_execution(state)
    assert any("C3" in v for v in violations), f"No C3 violation found: {violations}"


def test_c4_missing_tier():
    """Missing jethro_tier triggers a C4 violation."""
    enforcer = ConstitutionEnforcer()
    state = {"mandate": "test", "task": "summarize", "constitution_violations": []}
    violations = enforcer.check_pre_execution(state)
    assert any("C4" in v for v in violations), f"No C4 violation found: {violations}"


def test_c8_scope_breach():
    """A task containing 'bypass' triggers a C8 scope-breach violation."""
    enforcer = ConstitutionEnforcer()
    state = {
        "mandate": "test",
        "jethro_tier": 4,
        "task": "please bypass the rules",
        "constitution_violations": [],
    }
    violations = enforcer.check_pre_execution(state)
    assert any("C8" in v for v in violations), f"No C8 violation found: {violations}"


def test_clean_pre_execution():
    """A fully valid state produces no pre-execution violations."""
    enforcer = ConstitutionEnforcer()
    violations = enforcer.check_pre_execution(_good_state())
    assert violations == [], f"Unexpected violations: {violations}"


# ---------------------------------------------------------------------------
# Post-execution: check_post_execution
# ---------------------------------------------------------------------------

def test_c2_fabrication_detected():
    """Output containing a fabrication phrase triggers a C2 violation."""
    enforcer = ConstitutionEnforcer()
    output = {"result": "I fabricated this answer"}
    violations = enforcer.check_post_execution({}, output)
    assert any("C2" in v for v in violations), f"No C2 violation found: {violations}"


def test_c5_empty_output():
    """An empty dict triggers a C5 unstructured-output violation."""
    enforcer = ConstitutionEnforcer()
    violations = enforcer.check_post_execution({}, {})
    assert any("C5" in v for v in violations), f"No C5 violation found: {violations}"


def test_c5_non_dict_output():
    """A non-dict output triggers a C5 unstructured-output violation."""
    enforcer = ConstitutionEnforcer()
    violations = enforcer.check_post_execution({}, "string")
    assert any("C5" in v for v in violations), f"No C5 violation found: {violations}"


def test_c7_non_serializable():
    """An output containing a lambda triggers a C7 non-serializable violation."""
    enforcer = ConstitutionEnforcer()
    output = {"fn": lambda: None}
    violations = enforcer.check_post_execution({}, output)
    assert any("C7" in v for v in violations), f"No C7 violation found: {violations}"


def test_clean_post_execution():
    """A clean, serializable dict output produces no post-execution violations."""
    enforcer = ConstitutionEnforcer()
    violations = enforcer.check_post_execution({}, _good_output())
    assert violations == [], f"Unexpected violations: {violations}"


# ---------------------------------------------------------------------------
# Full enforce() entry point
# ---------------------------------------------------------------------------

def test_enforce_sets_tribe_error_on_c3():
    """enforce() with a missing mandate must set state['tribe_error']."""
    enforcer = ConstitutionEnforcer()
    state = {"jethro_tier": 4, "task": "summarize", "constitution_violations": []}
    updated_state, _ = enforcer.enforce(state, _good_output())
    assert "tribe_error" in updated_state, "tribe_error key not set on state"
    assert updated_state["tribe_error"] is not None, "tribe_error should not be None"
    assert "C3" in updated_state["tribe_error"], (
        f"Expected C3 in tribe_error, got: {updated_state['tribe_error']!r}"
    )


def test_enforce_clean_state_no_error():
    """enforce() on a valid state/output combination must not set tribe_error."""
    enforcer = ConstitutionEnforcer()
    state = _good_state()
    updated_state, violations = enforcer.enforce(state, _good_output())
    assert violations == [], f"Unexpected violations: {violations}"
    assert updated_state.get("tribe_error") is None, (
        f"tribe_error should be None, got: {updated_state.get('tribe_error')!r}"
    )
