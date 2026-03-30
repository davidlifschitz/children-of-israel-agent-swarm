"""hermes_node.py
LangGraph node that wraps Hermes Agent as a parallel Tier 4 executor.

Architecture:
  - Called by composer.py when a task is routed to a hermes_eligible tribe
  - Enforces constitution pre/post filters (Commandments 2, 3, 5, 7, 8)
  - Invokes Hermes CLI in non-interactive, no-learn, JSON-output mode
  - Returns structured output back into AgentState
  - On failure, signals fallback to original tribal node

Jethro Tier: 4 (leaf executor)
Parallel to: Naphtali, Reuben, Asher (hermes_eligible tribes)
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any

import yaml

from .agent_state import AgentState

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

with open("config/hermes_pipeline.yaml", "r") as _f:
    _HERMES_CFG = yaml.safe_load(_f)["hermes_pipeline"]

_TIMEOUT = _HERMES_CFG["cli"]["timeout_seconds"]
_TRIBE_SKILL_MAP = _HERMES_CFG["tribe_skill_map"]
_FALLBACK_POLICY = _HERMES_CFG["fallback_policy"]


# ---------------------------------------------------------------------------
# Constitution enforcement helpers
# ---------------------------------------------------------------------------

class ConstitutionViolation(Exception):
    """Raised when a Hermes output violates a hard commandment."""
    def __init__(self, commandment_id: int, detail: str):
        self.commandment_id = commandment_id
        super().__init__(f"[Commandment {commandment_id}] {detail}")


def _enforce_pre_call(state: AgentState, tribe_id: str) -> None:
    """Pre-call checks: Commandments 3 and 8."""
    # Commandment 3: task must have an explicit swarm mandate
    if not state.get("mandate"):
        raise ConstitutionViolation(
            3,
            f"No explicit mandate found in AgentState for tribe '{tribe_id}'. "
            "Hermes call blocked — unauthorized action."
        )
    # Commandment 8: tribe must be hermes_eligible
    if tribe_id not in _TRIBE_SKILL_MAP:
        raise ConstitutionViolation(
            8,
            f"Tribe '{tribe_id}' is not hermes_eligible. "
            "Task exceeds Hermes node scope."
        )


def _enforce_post_call(raw_output: str, original_input: str, tribe_id: str) -> dict[str, Any]:
    """Post-call checks: Commandments 2, 5, 7. Returns parsed output."""
    # Commandment 5: output must be valid structured JSON
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ConstitutionViolation(
            5,
            f"Hermes output for tribe '{tribe_id}' is not valid JSON. "
            f"Cannot verify clarity or integrity. Raw: {raw_output[:200]}"
        ) from exc

    # Commandment 2: output must not self-report hallucination or uncertainty as fact
    # (Hermes --json-output includes a `grounded` boolean when available)
    if isinstance(parsed, dict) and parsed.get("grounded") is False:
        raise ConstitutionViolation(
            2,
            f"Hermes flagged its own output as ungrounded for tribe '{tribe_id}'. "
            "Fabrication check failed."
        )

    # Commandment 7: log any transformations (input vs output keys diff)
    if isinstance(parsed, dict):
        transforms = {
            "input_length": len(original_input),
            "output_keys": list(parsed.keys()),
            "tribe": tribe_id,
            "timestamp": time.time(),
        }
        parsed["__transform_log"] = transforms

    return parsed


# ---------------------------------------------------------------------------
# Hermes CLI invocation
# ---------------------------------------------------------------------------

def _build_hermes_cmd(task: str, tribe_id: str) -> list[str]:
    """Build the Hermes CLI command for a given task and tribe."""
    tribe_cfg = _TRIBE_SKILL_MAP[tribe_id]
    skill_names = [s["name"] for s in tribe_cfg["skills"]]

    cmd = [
        "hermes",
        "run",
        "--non-interactive",
        "--no-learn",           # Commandment 3: no autonomous improvement inside swarm
        "--json-output",        # Commandment 5: structured output required
        "--timeout", str(tribe_cfg.get("max_latency_seconds", _TIMEOUT)),
    ]

    # Attach tribe-appropriate skills
    for skill in skill_names:
        cmd.extend(["--skill", skill])

    cmd.extend(["--task", task])
    return cmd


def _call_hermes(task: str, tribe_id: str) -> str:
    """Invoke Hermes CLI and return raw stdout."""
    cmd = _build_hermes_cmd(task, tribe_id)
    tribe_timeout = _TRIBE_SKILL_MAP[tribe_id].get("max_latency_seconds", _TIMEOUT)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=tribe_timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Hermes CLI exited with code {result.returncode}. "
            f"stderr: {result.stderr[:500]}"
        )

    return result.stdout


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------

def hermes_node(state: AgentState) -> AgentState:
    """LangGraph node: Hermes parallel pipeline executor.

    Called by composer.py when routing to a hermes_eligible tribe.
    Enforces the Ten Commandments as pre/post filters.
    Returns updated AgentState on success, or sets hermes_fallback=True on failure.
    """
    tribe_id: str = state.get("current_tribe", "")
    task: str = state.get("task", "")

    # --- Pre-call constitution enforcement (Commandments 3, 8) ---
    try:
        _enforce_pre_call(state, tribe_id)
    except ConstitutionViolation as exc:
        # Commandment 6: escalate what you cannot resolve
        return {
            **state,
            "hermes_fallback": True,
            "hermes_error": str(exc),
            "escalate": True,
            "escalation_reason": str(exc),
        }

    # --- Hermes CLI call ---
    try:
        raw_output = _call_hermes(task, tribe_id)
    except subprocess.TimeoutExpired:
        if _FALLBACK_POLICY["on_timeout"] == "return_to_tribe":
            return {**state, "hermes_fallback": True, "hermes_error": "timeout"}
        return {**state, "hermes_fallback": True, "hermes_error": "timeout", "escalate": True}
    except RuntimeError as exc:
        if _FALLBACK_POLICY["on_error"] == "return_to_tribe":
            return {**state, "hermes_fallback": True, "hermes_error": str(exc)}
        return {**state, "hermes_fallback": True, "hermes_error": str(exc), "escalate": True}

    # --- Post-call constitution enforcement (Commandments 2, 5, 7) ---
    try:
        parsed_output = _enforce_post_call(raw_output, task, tribe_id)
    except ConstitutionViolation as exc:
        if _FALLBACK_POLICY["on_constitution_violation"] == "escalate":
            return {
                **state,
                "hermes_fallback": True,
                "hermes_error": str(exc),
                "escalate": True,
                "escalation_reason": str(exc),
            }
        return {**state, "hermes_fallback": True, "hermes_error": str(exc)}

    # --- Success: merge Hermes output into AgentState ---
    return {
        **state,
        "hermes_output": parsed_output,
        "hermes_fallback": False,
        "hermes_error": None,
        "output": parsed_output,   # surface to downstream nodes
    }
