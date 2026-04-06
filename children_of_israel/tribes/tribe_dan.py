"""tribe_dan.py — Dan: Judge / Arbitrator
Tier 1 senior. Domain: Conflict resolution, edge case adjudication.
Hermes eligible: no

BUG 1 fix: sets next_node=None on exit.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer
from children_of_israel.oral_law_engine import oral_law_engine
from children_of_israel.precedent_store import precedent_store

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
  Set precedent_set=true for novel conflict types.

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
    try:
        prior_precedents = precedent_store.lookup(state.get("task", "")[:50])
        if prior_precedents:
            precedent_context = "\n\nPrior precedents for similar conflicts:\n" + "\n".join(
                f"- [{p['id']}] {p['ruling']}" for p in prior_precedents[:3]
            )
        else:
            precedent_context = ""
        result = llm_call("dan", SYSTEM_PROMPT, escalation_reason + precedent_context)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe
        existing_precedents = list(state.get("oral_law_precedents") or [])
        precedent_id = f"DAN-{len(existing_precedents) + 1:04d}"
        if result.get("precedent_set"):
            result["precedent_id"] = precedent_id
            existing_precedents = existing_precedents + [precedent_id]
        should_escalate = result.get("ruling") == "escalate_to_moses"
        conflict_type = state.get("task", "general")[:50]
        ruling_summary = result.get("ruling", result.get("output", str(result)))[:200]
        oral_law_engine.log_precedent(state, conflict_type, ruling_summary)
        return {
            **state,
            "current_tribe": "dan",
            "jethro_tier": 1,
            "oral_law_precedents": existing_precedents,
            "tribe_output": result,
            "output": result,
            "next_node": None,   # BUG 1 fix
            "tribe_error": None,
            "escalate": should_escalate,
            "escalation_reason": None,
        }
    except Exception as exc:
        return {**state, "current_tribe": "dan", "tribe_error": str(exc), "next_node": None}
