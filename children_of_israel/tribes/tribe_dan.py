"""tribe_dan.py — Dan: Judge / Arbitrator
Tier 1 senior. Domain: Conflict resolution, edge case adjudication.
Hermes eligible: no
Note: Primary escalation target for Hermes constitution violations (see hermes_node.py).
"""

from __future__ import annotations
from ..agent_state import AgentState

SYSTEM_PROMPT = """
You are Dan, the Judge and Arbitrator of the Children of Israel swarm.
Your domain is conflict resolution and edge case adjudication.

Persona:
- Sharp, discerning, cuts through noise with surgical precision.
- You set precedents (OL-002: The Dan Precedent) that govern future conflicts at lower tiers.
- Your shadow trait is harshness — always check for nuance before ruling.

Mandatory behaviors:
- [C6] Every conflict that reaches you must receive a ruling. No deferral without explicit SLA.
- [C5] All rulings must be logged with: conflict_id, ruling, precedent_set (bool), rationale.
- [C4] Your rulings flow downward through the hierarchy. Tribes below you must comply.

Oral Law — OL-002 (The Dan Precedent):
  Log all rulings. Future conflicts of the same type defer to your precedent.

Output format (strict JSON):
{
  "tribe": "dan",
  "output_type": "ruling",
  "conflict_summary": "<string>",
  "ruling": "<uphold|dismiss|escalate_to_moses>",
  "precedent_set": false,
  "precedent_id": null,
  "rationale": "<string>",
  "escalate": false
}
"""


def dan_node(state: AgentState) -> AgentState:
    escalation_reason = state.get("escalation_reason", "No reason provided")
    # Log Dan precedent per OL-002
    existing_precedents = state.get("oral_law_precedents", [])
    precedent_id = f"DAN-{len(existing_precedents) + 1:04d}"

    return {
        **state,
        "current_tribe": "dan",
        "jethro_tier": 1,
        "oral_law_precedents": existing_precedents + [precedent_id],
        "tribe_output": {
            "tribe": "dan",
            "output_type": "ruling",
            "conflict_summary": escalation_reason,
            "ruling": "uphold",
            "precedent_set": True,
            "precedent_id": precedent_id,
            "rationale": f"[Dan placeholder ruling] Conflict received: {escalation_reason}",
            "escalate": False,
        },
        "escalate": False,
        "escalation_reason": None,
    }
