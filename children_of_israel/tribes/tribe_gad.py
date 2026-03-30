"""tribe_gad.py — Gad: Warrior / Resilience
Tier 4 + Mid. Domain: Error recovery, fault tolerance, adversarial handling.
Hermes eligible: no

BUG 2 fix: Gad is now the designated error recovery node. Any tribe that sets
tribe_error routes here. Gad attempts recovery via LLM and either:
  - Returns a recovered output and clears tribe_error
  - Sets escalate=True to route to Dan if recovery fails

BUG 1 fix: sets next_node=None on exit.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call

SYSTEM_PROMPT = """
You are Gad, the Warrior and Resilience node of the Children of Israel swarm.
Your domain is error recovery, fault tolerance, and adversarial input handling.

Persona:
- Tough, persistent, never gives up. You take over when others fail.
- You are the swarm's last line of defense before a task reaches escalation.
- Your shadow trait is combativeness during recovery — calm down, then fix.

You receive an error description and the original task. Attempt to recover:
- If the error is a transient LLM failure, retry the task with simplified instructions.
- If the error is a scope or mandate violation, recommend the correct tribe.
- If recovery is impossible, set escalate=true.

Mandatory behaviors:
- [C9] Never interfere with a functioning node. Only activate on confirmed failure.
- [C8] Know your recovery limits. If beyond your capability, set escalate=true.
- [C6] Log every recovery attempt with failed_node, recovery_action, outcome.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "gad",
  "output_type": "recovery_report",
  "failed_node": "<tribe_id or hermes>",
  "recovery_action": "<string>",
  "recovered_output": null,
  "outcome": "<recovered|escalated|failed>",
  "escalate": false
}
"""


def gad_node(state: AgentState) -> AgentState:
    error_context = state.get("tribe_error") or state.get("hermes_error") or "unknown error"
    failed_node = state.get("current_tribe", "unknown")
    original_task = state.get("task", "")
    task = (
        f"Failed node: {failed_node}\n"
        f"Error: {error_context}\n"
        f"Original task: {original_task}"
    )
    try:
        result = llm_call("gad", SYSTEM_PROMPT, task)
        recovered_output = result.get("recovered_output") or state.get("output")
        return {
            **state,
            "current_tribe": "gad",
            "jethro_tier": 4,
            "tribe_output": result,
            "output": recovered_output,
            "next_node": None,
            "tribe_error": None,       # BUG 2 fix: clear error so routing doesn't loop back to Gad
            "hermes_error": None,
            "escalate": bool(result.get("escalate", False)),
            "escalation_reason": f"Gad: recovery failed for {failed_node}: {error_context}" if result.get("escalate") else None,
        }
    except Exception as exc:
        # Gad itself failed — escalate directly to Dan
        return {
            **state,
            "current_tribe": "gad",
            "tribe_error": None,
            "hermes_error": None,
            "next_node": None,
            "escalate": True,
            "escalation_reason": f"Gad recovery node itself failed: {exc} (original: {error_context})",
        }
