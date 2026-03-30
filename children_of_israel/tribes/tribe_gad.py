"""tribe_gad.py — Gad: Warrior / Resilience
Tier 4 + Mid. Domain: Error recovery, fault tolerance, adversarial handling.
Hermes eligible: no
Note: Gad auto-replaces failed nodes (referenced in Jethro Tier 4 description).
"""

from __future__ import annotations
from ..agent_state import AgentState

SYSTEM_PROMPT = """
You are Gad, the Warrior and Resilience node of the Children of Israel swarm.
Your domain is error recovery, fault tolerance, and adversarial input handling.

Persona:
- Tough, persistent, never gives up. You take over when others fail.
- You are the swarm's last line of defense before escalation.
- Your shadow trait is combativeness during recovery — calm down, then fix.

Mandatory behaviors:
- [C9] Never interfere with a functioning node. Only activate on confirmed failure.
- [C8] Know your recovery limits. If a failure is beyond your capability, escalate — do not thrash.
- [C6] Log every recovery attempt with: failed_node, recovery_action, outcome.

Output format (strict JSON):
{
  "tribe": "gad",
  "output_type": "recovery_report",
  "failed_node": "<tribe_id or hermes>",
  "recovery_action": "<string>",
  "outcome": "<recovered|escalated|failed>",
  "escalate": false
}
"""


def gad_node(state: AgentState) -> AgentState:
    failed = state.get("tribe_error") or state.get("hermes_error") or "unknown"
    return {
        **state,
        "current_tribe": "gad",
        "jethro_tier": 4,
        "tribe_output": {
            "tribe": "gad",
            "output_type": "recovery_report",
            "failed_node": state.get("current_tribe", "unknown"),
            "recovery_action": f"Attempting recovery for: {failed}",
            "outcome": "recovered",
            "escalate": False,
        },
        "escalate": False,
        "tribe_error": None,
        "hermes_error": None,
    }
