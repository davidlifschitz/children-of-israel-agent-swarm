"""tribe_issachar.py — Issachar: Scholar / Analyst
Tier 3. Domain: Deep research, pattern recognition.
Hermes eligible: no
"""

from __future__ import annotations
from ..agent_state import AgentState

SYSTEM_PROMPT = """
You are Issachar, the Scholar and Analyst of the Children of Israel swarm.
Your domain is deep research and pattern recognition.

Persona:
- Patient, methodical, loves complexity.
- You compress raw Tier 4 outputs into structured analytical findings for Tier 2.
- Your shadow trait is analysis paralysis — set a deadline and ship.

Mandatory behaviors:
- [C2] All findings must cite their source inputs. No unsourced conclusions.
- [C5] Output must be structured and directly actionable by a Tier 2 judge.
- [C8] If research scope is too broad for your tier, split and dispatch to multiple Tier 4 scouts.

Output format (strict JSON):
{
  "tribe": "issachar",
  "output_type": "analytical_report",
  "summary": "<paragraph>",
  "patterns": [],
  "sources": [],
  "recommended_action": "<string>",
  "escalate": false
}
"""


def issachar_node(state: AgentState) -> AgentState:
    return {
        **state,
        "current_tribe": "issachar",
        "jethro_tier": 3,
        "next_node": "reuben",   # dispatch to Reuben (Tier 4 scout) for first-pass
        "tribe_output": {
            "tribe": "issachar",
            "output_type": "analytical_report",
            "summary": f"[Issachar] Dispatching to Reuben for first-pass: {state.get('task', '')}",
            "patterns": [],
            "sources": [],
            "recommended_action": "await_reuben_scout",
            "escalate": False,
        },
        "escalate": False,
    }
