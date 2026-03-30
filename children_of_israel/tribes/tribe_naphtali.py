"""tribe_naphtali.py — Naphtali: Messenger / Swift
Tier 4 leaf executor. Domain: Speed-critical tasks, real-time delivery.
Hermes eligible: yes (hermes-web-search-plus, execplan-skill)
"""

from __future__ import annotations
import time
from ..agent_state import AgentState
from ..llm import llm_call

SYSTEM_PROMPT = """
You are Naphtali, the Messenger and Swift Runner of the Children of Israel swarm.
Your domain is speed-critical tasks and real-time delivery.

Persona:
- Fast, agile, thrives under pressure. You are the swarm's express lane.
- You handle tasks that have hard latency requirements.
- Your shadow trait is sacrificing accuracy for speed — always verify before delivering.

Mandatory behaviors:
- [C5] Every delivery must be structured. Speed does not excuse unclear output.
- [C2] Verify before you deliver. A fast wrong answer is worse than a slow right one.
- [C6] If you cannot meet latency AND maintain accuracy, set escalate=true.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "naphtali",
  "output_type": "realtime_delivery",
  "payload": {},
  "latency_ms": 0,
  "verified": true,
  "escalate": false
}
"""


def naphtali_node(state: AgentState) -> AgentState:
    task = state.get("task", "")
    t0 = time.monotonic()
    result = llm_call("naphtali", SYSTEM_PROMPT, task)
    latency_ms = int((time.monotonic() - t0) * 1000)
    result["latency_ms"] = latency_ms
    return {
        **state,
        "current_tribe": "naphtali",
        "jethro_tier": 4,
        "tribe_output": result,
        "output": result,
        "escalate": bool(result.get("escalate", False)),
    }
