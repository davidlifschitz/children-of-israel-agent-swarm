"""tribe_asher.py — Asher: Optimizer / Enricher
Tier 3. Domain: Output quality, refinement, polishing.
Hermes eligible: yes (maestro, execplan-skill)

BUG 1 fix: sets next_node=None on exit.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer
from children_of_israel.commandment_advisor import advisor as _advisor

SYSTEM_PROMPT = """
You are Asher, the Optimizer and Enricher of the Children of Israel swarm.
Your domain is output quality, refinement, and polishing.

Persona:
- Aesthetic and detail-loving. You make good outputs great.
- You are the final pass before output reaches Tier 2 judges.
- Your shadow trait is perfectionism — ship when it is good enough, not when it is perfect.

You receive the current swarm output. Refine its clarity, structure, and quality.

Mandatory behaviors:
- [C7] Never alter the factual substance of what you refine. Style and structure only.
- [C5] Your output must be more structured and clear than your input.
- [C8] If refinement would require changing facts, set escalate=true and flag it.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "asher",
  "output_type": "refined_output",
  "original_summary": "<string>",
  "refined_summary": "<string>",
  "changes_made": ["<change 1>"],
  "quality_score": 0.95,
  "escalate": false
}
"""


def asher_node(state: AgentState) -> AgentState:
    raw = state.get("output") or state.get("tribe_output", {})
    task = raw.get("summary", str(raw)) if isinstance(raw, dict) else str(raw)
    try:
        _directives = _advisor.format_for_prompt(_advisor.get_directives_for_tribe("asher"))
        if _directives:
            system_prompt = _directives + "\n\n" + SYSTEM_PROMPT
        else:
            system_prompt = SYSTEM_PROMPT
        result = llm_call("asher", system_prompt, task)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe
        return {
            **state,
            "current_tribe": "asher",
            "jethro_tier": 3,
            "tribe_output": result,
            "output": result,
            "next_node": None,
            "tribe_error": None,
            "escalate": bool(result.get("escalate", False)),
            "escalation_reason": "Asher: fact change required during refinement" if result.get("escalate") else None,
        }
    except Exception as exc:
        return {**state, "current_tribe": "asher", "tribe_error": str(exc), "next_node": None}
