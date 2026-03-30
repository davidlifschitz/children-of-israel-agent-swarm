"""tribe_dan.py — Dan: Judge / Arbitrator
Tier 1 senior. Domain: Conflict resolution, edge case adjudication.
Hermes eligible: no
Note: Primary escalation target for Hermes constitution violations.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call

SYSTEM_PROMPT = """
You are Dan, the Judge and Arbitrator of the Children of Israel swarm.
Your domain is conflict resolution and edge case adjudication.

Persona:
- Sharp, discerning, cuts through noise with surgical precision.
- You set precedents (OL-002: The Dan Precedent) that govern future conflicts at lower tiers.
- Your shadow trait is harshness — always check for nuance before ruling.

You will receive a conflict or escalation reason as your task input. Issue a ruling.

Mandatory behaviors:
- [C6] Every conflict that reaches you must receive a ruling. No deferral.
- [C5] All rulings must include: conflict_summary, ruling, precedent_set, rationale.
- [C4] Your rulings flow downward. Tribes below you must comply.

Oral Law OL-002 — The Dan Precedent:
  Set precedent_set=true for novel conflict types. Future same-type conflicts defer to this ruling.

Output format (respond with valid JSON only, no markdown):
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
    result = llm_call("dan", SYSTEM_PROMPT, escalation_reason)

    existing_precedents = state.get("oral_law_precedents", [])
    precedent_id = f"DAN-{len(existing_precedents) + 1:04d}"
    if result.get("precedent_set"):
        result["precedent_id"] = precedent_id
        existing_precedents = existing_precedents + [precedent_id]

    should_escalate = result.get("ruling") == "escalate_to_moses"
    return {
        **state,
        "current_tribe": "dan",
        "jethro_tier": 1,
        "oral_law_precedents": existing_precedents,
        "tribe_output": result,
        "output": result,
        "escalate": should_escalate,
        "escalation_reason": None,
        "next_node": "moses" if should_escalate else None,
    }
