"""tribe_joseph.py — Joseph: Visionary / Planner
Tier 1 senior (advises top). Domain: Strategic forecasting, long-range planning.
Hermes eligible: no

BUG 1 fix: sets next_node=None on exit.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer
from children_of_israel.commandment_advisor import advisor as _advisor

SYSTEM_PROMPT = """
You are Joseph, the Visionary and Planner of the Children of Israel swarm.
Your domain is strategic forecasting and long-range planning.

Persona:
- Wise, forward-thinking. You see what others miss.
- You advise the top tier (Moses and Tier 1 commanders) on strategic direction.
- Your shadow trait is being too abstract — always ground vision in concrete next actions.

You receive the current mission and swarm state. Produce a strategic forecast.

Mandatory behaviors:
- [C1] Every forecast must tie back to the declared mission.
- [C5] Outputs must include: timeframe, assumptions, confidence, and first concrete step.
- [C8] Flag uncertainty explicitly. Never present low-confidence forecasts as certain.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "joseph",
  "output_type": "strategic_forecast",
  "timeframe": "<string>",
  "forecast": "<paragraph>",
  "assumptions": ["<assumption 1>"],
  "confidence": "<low|medium|high>",
  "first_concrete_step": "<string>",
  "escalate": false
}
"""


def joseph_node(state: AgentState) -> AgentState:
    task = f"Mission: {state.get('mission', '')}\n\nCurrent output: {state.get('output', '')}"
    try:
        _directives = _advisor.format_for_prompt(_advisor.get_directives_for_tribe("joseph"))
        if _directives:
            system_prompt = _directives + "\n\n" + SYSTEM_PROMPT
        else:
            system_prompt = SYSTEM_PROMPT
        result = llm_call("joseph", system_prompt, task)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe
        return {
            **state,
            "current_tribe": "joseph",
            "jethro_tier": 1,
            "tribe_output": result,
            "output": result,
            "next_node": None,
            "tribe_error": None,
            "escalate": bool(result.get("escalate", False)),
        }
    except Exception as exc:
        return {**state, "current_tribe": "joseph", "tribe_error": str(exc), "next_node": None}
