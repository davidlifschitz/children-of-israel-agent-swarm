"""tribe_asher.py — Asher: Optimizer / Enricher
Tier 3. Domain: Output quality, refinement, polishing.
Hermes eligible: yes (maestro, execplan-skill)
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call

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
    result = llm_call("asher", SYSTEM_PROMPT, task)
    return {
        **state,
        "current_tribe": "asher",
        "jethro_tier": 3,
        "tribe_output": result,
        "output": result,
        "escalate": bool(result.get("escalate", False)),
        "escalation_reason": "Asher: fact change required" if result.get("escalate") else None,
    }
