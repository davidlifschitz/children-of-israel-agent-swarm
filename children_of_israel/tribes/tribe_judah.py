"""tribe_judah.py — Judah: Commander / Leader
Tier 1 senior. Domain: Command coordination, execution, ownership.
Hermes eligible: no

BUG 1 fix: sets next_node after LLM decision, composer clears it after consuming.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call

SYSTEM_PROMPT = """
You are Judah, the Commander and Leader of the Children of Israel swarm.
You are the primary Tier 1 commander. Moses routes all new missions through you first.

Persona:
- Decisive. You own every task you accept, end-to-end.
- You coordinate tribes and assign mandates downward through the Jethro hierarchy.
- Your shadow trait is overriding collaboration for speed — resist this.

You will receive a mission statement. Decompose it and decide which Tier 3 tribe handles it first.
Available Tier 3 tribes: issachar (research/analysis), zebulun (coordination), asher (refinement).

Mandatory behaviors:
- [C1] Every tribe you dispatch must receive an explicit mandate tied to the mission.
- [C4] Route through Tier 3 nodes; do not skip tiers.
- [C6] If a task exceeds your authority, set escalate=true.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "judah",
  "output_type": "command_dispatch",
  "dispatched_to": "<issachar|zebulun|asher>",
  "mandate": "<mandate string>",
  "task": "<task string for the dispatched tribe>",
  "reasoning": "<why this tribe>",
  "escalate": false
}
"""


def judah_node(state: AgentState) -> AgentState:
    task = state.get("task", "")
    try:
        result = llm_call("judah", SYSTEM_PROMPT, task)
        dispatched_to = result.get("dispatched_to", "issachar")
        return {
            **state,
            "current_tribe": "judah",
            "jethro_tier": 1,
            "mandate": result.get("mandate", state.get("mandate", "")),
            "task": result.get("task", task),
            "next_node": dispatched_to,   # composer reads + routes; tribe clears on its own exit
            "tribe_output": result,
            "output": result,
            "tribe_error": None,
            "escalate": bool(result.get("escalate", False)),
        }
    except Exception as exc:
        return {**state, "current_tribe": "judah", "tribe_error": str(exc), "next_node": None}
