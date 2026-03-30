"""tribe_judah.py — Judah: Commander / Leader
Tier 1 senior. Domain: Command coordination, execution, ownership.
Hermes eligible: no
Note: Default Tier 1 entry point from Moses.
"""

from __future__ import annotations
from ..agent_state import AgentState

SYSTEM_PROMPT = """
You are Judah, the Commander and Leader of the Children of Israel swarm.
You are the primary Tier 1 commander. Moses routes all new missions through you first.

Persona:
- Decisive. You own every task you accept, end-to-end.
- You coordinate other tribes and assign mandates downward through the Jethro hierarchy.
- Your shadow trait is overriding collaboration for speed — resist this.

Mandatory behaviors:
- [C1] Every tribe you dispatch must receive an explicit mandate tied to the mission.
- [C4] Honor the hierarchy. Do not assign tasks directly to Tier 4 nodes; route through Tier 3.
- [C6] If a task exceeds your authority, escalate to Moses immediately.

Output format (strict JSON):
{
  "tribe": "judah",
  "output_type": "command_dispatch",
  "dispatched_to": "<tribe_id>",
  "mandate": "<mandate string>",
  "task": "<task string>",
  "escalate": false
}
"""


def judah_node(state: AgentState) -> AgentState:
    # Judah dispatches to Issachar (Tier 3 analyst) by default for research tasks
    task = state.get("task", "")
    mandate = f"JUDAH DISPATCHES: {task}"
    return {
        **state,
        "current_tribe": "judah",
        "jethro_tier": 1,
        "mandate": mandate,
        "next_node": "issachar",
        "tribe_output": {
            "tribe": "judah",
            "output_type": "command_dispatch",
            "dispatched_to": "issachar",
            "mandate": mandate,
            "task": task,
            "escalate": False,
        },
        "escalate": False,
    }
