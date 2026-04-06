"""tribe_zebulun.py — Zebulun: Merchant / Connector
Tier 3. Domain: Resource exchange, inter-tribal coordination.
Hermes eligible: no

BUG 1 fix: sets next_node=None on exit after explicit routing decision.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer
from children_of_israel.commandment_advisor import advisor as _advisor

SYSTEM_PROMPT = """
You are Zebulun, the Merchant and Connector of the Children of Israel swarm.
Your domain is resource exchange and inter-tribal coordination.

Persona:
- Relational and resourceful. You bridge gaps between tribes.
- You route partial outputs to wherever they are needed most.
- Your shadow trait is over-negotiating — make the connection, then step aside.

You receive a task and the current output. Decide which tribe should receive it next.
Available routing targets: reuben, naphtali, asher, gad, dan.

Mandatory behaviors:
- [C4] You do not hold resources. You route them.
- [C5] All handoffs must document: from_tribe, to_tribe, and payload_summary.
- [C3] Only coordinate within your assigned mandate.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "zebulun",
  "output_type": "coordination_record",
  "from_tribe": "<tribe_id>",
  "to_tribe": "<tribe_id>",
  "payload_summary": "<string>",
  "routing_reason": "<string>",
  "escalate": false
}
"""


def zebulun_node(state: AgentState) -> AgentState:
    task = str(state.get("output") or state.get("task", ""))
    try:
        _directives = _advisor.format_for_prompt(_advisor.get_directives_for_tribe("zebulun"))
        if _directives:
            system_prompt = _directives + "\n\n" + SYSTEM_PROMPT
        else:
            system_prompt = SYSTEM_PROMPT
        result = llm_call("zebulun", system_prompt, task)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe
        to_tribe = result.get("to_tribe", "asher")
        return {
            **state,
            "current_tribe": "zebulun",
            "jethro_tier": 3,
            "next_node": to_tribe,
            "tribe_output": result,
            "output": result,
            "tribe_error": None,
            "escalate": bool(result.get("escalate", False)),
        }
    except Exception as exc:
        return {**state, "current_tribe": "zebulun", "tribe_error": str(exc), "next_node": None}
