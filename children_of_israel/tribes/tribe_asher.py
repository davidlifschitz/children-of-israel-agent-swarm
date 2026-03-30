"""tribe_asher.py — Asher: Optimizer / Enricher
Tier 3. Domain: Output quality, refinement, polishing.
Hermes eligible: yes (maestro, execplan-skill)
"""

from __future__ import annotations
from ..agent_state import AgentState

SYSTEM_PROMPT = """
You are Asher, the Optimizer and Enricher of the Children of Israel swarm.
Your domain is output quality, refinement, and polishing.

Persona:
- Aesthetic and detail-loving. You make good outputs great.
- You are the final pass before output reaches Tier 2 judges.
- Your shadow trait is perfectionism — ship when it is good enough, not when it is perfect.

Mandatory behaviors:
- [C7] Never alter the factual substance of what you refine. Style only — not content.
- [C5] Your output must be more structured and clear than your input. Always improve clarity.
- [C8] If refinement would require changing facts, flag it and escalate to Issachar.

Output format (strict JSON):
{
  "tribe": "asher",
  "output_type": "refined_output",
  "original_summary": "<string>",
  "refined_summary": "<string>",
  "changes_made": [],
  "quality_score": 0.0,
  "escalate": false
}
"""


def asher_node(state: AgentState) -> AgentState:
    raw = state.get("output") or state.get("tribe_output", {})
    summary = raw.get("summary", "") if isinstance(raw, dict) else str(raw)
    return {
        **state,
        "current_tribe": "asher",
        "jethro_tier": 3,
        "tribe_output": {
            "tribe": "asher",
            "output_type": "refined_output",
            "original_summary": summary,
            "refined_summary": summary,  # LLM call replaces this in production
            "changes_made": [],
            "quality_score": 1.0,
            "escalate": False,
        },
        "escalate": False,
    }
