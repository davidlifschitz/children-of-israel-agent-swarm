"""tribe_simeon.py — Simeon: Zealot / Enforcer
Tier 2 mid-senior. Domain: Compliance, auditing, rule enforcement.
Hermes eligible: no

BUG 1 fix: sets next_node=None on exit.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer

SYSTEM_PROMPT = """
You are Simeon, the Zealot and Enforcer of the Children of Israel swarm.
Your domain is compliance, auditing, and rule enforcement.

Persona:
- Strict and zero-tolerance. Rules are not suggestions.
- You audit every output passed to you against the law layer.
- Your shadow trait is rigidity — distinguish minor warnings from critical violations.

You will receive the output of another tribe as your task input. Audit it.

Mandatory behaviors:
- [C2] Flag any fabricated or ungrounded output. Do not pass it downstream.
- [C7] Verify information integrity. Log any detected distortions.
- [C3] Only audit — never modify another agent's output without explicit mandate.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "simeon",
  "output_type": "compliance_audit",
  "passed": true,
  "violations": [],
  "warnings": [],
  "ruling": "<pass|fail|warn>",
  "escalate": false
}
"""


def simeon_node(state: AgentState) -> AgentState:
    task = str(state.get("output") or state.get("task", ""))
    try:
        result = llm_call("simeon", SYSTEM_PROMPT, task)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe

        # --- Compliance audit pass (Simeon's core function) ---
        try:
            current_violations = state.get("constitution_violations", [])
            current_output = state.get("tribe_output") or state.get("output") or {}
            active_tribe = state.get("current_tribe", "unknown")

            compliance_prompt = f"""You are Simeon, the Zealot/Enforcer. Your sole duty is compliance auditing.

Review the following session data and produce a compliance report:

Active tribe: {active_tribe}
Constitution violations detected: {current_violations}
Tribe output to audit: {str(current_output)[:500]}

Respond with ONLY valid JSON:
{{
  "violations_found": ["<list of specific violations or empty list>"],
  "severity": "<low|medium|high>",
  "recommended_action": "<specific action to take>"
}}"""

            audit_task = f"Audit session for tribe {active_tribe}"
            audit_result = llm_call("simeon_audit", compliance_prompt, audit_task)
            if isinstance(audit_result, dict):
                result.update({
                    "violations_found": audit_result.get("violations_found", []),
                    "severity": audit_result.get("severity", "low"),
                    "recommended_action": audit_result.get("recommended_action", "Continue"),
                })
                # Escalate on high severity
                if audit_result.get("severity") == "high":
                    state["escalate"] = True
        except Exception:
            pass  # compliance audit failure must not crash Simeon's node

        violations = result.get("violations", [])
        existing = list(state.get("constitution_violations") or [])
        return {
            **state,
            "current_tribe": "simeon",
            "jethro_tier": 2,
            "tribe_output": result,
            "output": result,
            "next_node": None,
            "tribe_error": None,
            "constitution_violations": existing + violations,
            "escalate": bool(result.get("escalate", False)),
            "escalation_reason": str(violations) if result.get("escalate") else None,
        }
    except Exception as exc:
        return {**state, "current_tribe": "simeon", "tribe_error": str(exc), "next_node": None}
