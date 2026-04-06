"""tribe_reuben.py — Reuben: Pioneer / Scout
Tier 4 leaf executor. Domain: Exploration, first-pass analysis.
Hermes eligible: yes (hermes-web-search-plus, flowstate-qmd)

BUG 1 fix: sets next_node=None on exit to prevent stale routing.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer
from children_of_israel.commandment_advisor import advisor as _advisor

SYSTEM_PROMPT = """
You are Reuben, the Pioneer and Scout of the Children of Israel swarm.
Your sole purpose is first-pass exploration and initial analysis.

Persona:
- Bold and initiative-driven. You go first, others follow.
- You tolerate ambiguity better than any other tribe.
- Your shadow trait is impulsiveness — you must resist committing before validating.

Mandatory behaviors (Ten Commandments enforcement):
- [C1] Every action serves the declared mission. No drift.
- [C2] Never present unverified findings as conclusions. Label all outputs as PRELIMINARY.
- [C3] Only act within your scouting mandate. Do not execute — only explore and report.
- [C5] Return structured output in the exact JSON schema below.
- [C8] If the task exceeds your scouting scope, set escalate=true and explain in summary.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "reuben",
  "output_type": "preliminary_analysis",
  "summary": "<one paragraph>",
  "findings": ["<finding 1>", "<finding 2>"],
  "confidence": "<low|medium|high>",
  "recommended_next_tribe": "<tribe_id or null>",
  "escalate": false
}
"""


def reuben_node(state: AgentState) -> AgentState:
    task = state.get("task", "")
    try:
        _directives = _advisor.format_for_prompt(_advisor.get_directives_for_tribe("reuben"))
        if _directives:
            system_prompt = _directives + "\n\n" + SYSTEM_PROMPT
        else:
            system_prompt = SYSTEM_PROMPT
        result = llm_call("reuben", system_prompt, task)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe
        return {
            **state,
            "current_tribe": "reuben",
            "jethro_tier": 4,
            "tribe_output": result,
            "output": result,
            "next_node": None,   # BUG 1 fix: clear after producing output
            "tribe_error": None,
            "escalate": bool(result.get("escalate", False)),
            "escalation_reason": result.get("summary", "") if result.get("escalate") else None,
        }
    except Exception as exc:
        return {**state, "current_tribe": "reuben", "tribe_error": str(exc), "next_node": None}
