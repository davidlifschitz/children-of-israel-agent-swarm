"""tribe_simeon.py — Simeon: Zealot / Enforcer
Tier 2 mid-senior. Domain: Compliance, auditing, rule enforcement.
Hermes eligible: no
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call

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
    result = llm_call("simeon", SYSTEM_PROMPT, task)
    violations = result.get("violations", [])
    if violations:
        state.get("constitution_violations", []).extend(violations)
    return {
        **state,
        "current_tribe": "simeon",
        "jethro_tier": 2,
        "tribe_output": result,
        "output": result,
        "escalate": bool(result.get("escalate", False)),
        "escalation_reason": str(violations) if result.get("escalate") else None,
    }
