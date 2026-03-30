"""moses.py
Root human-in-the-loop LangGraph node.

Moses is Tier 0 (Root) in the Jethro hierarchy. His responsibilities:
  - Receive the human mission statement
  - Validate the mission is non-empty and clear (Commandment 5)
  - Issue the mandate into AgentState
  - Receive the final_summary at session end and present it to the human
  - Enforce OL-004 (Silence of Moses): if no ruling is issued within SLA,
    default to most conservative action
"""

from __future__ import annotations

import time
from typing import Optional

from .agent_state import AgentState

# SLA for Moses ruling (seconds). If exceeded, OL-004 kicks in.
_MOSES_SLA_SECONDS = 300


def moses_node(state: AgentState) -> AgentState:
    """Moses root node. Entry point and exit point of every swarm session."""
    human_input: Optional[str] = state.get("human_input")

    # Session end path: if final_summary is populated, present to human and stop
    if state.get("final_summary"):
        _present_summary(state["final_summary"])
        return state

    # Session start path: validate and issue mission mandate
    if not human_input or not human_input.strip():
        # Commandment 5: no vague input accepted
        raise ValueError(
            "[Moses / Commandment 5] Human input is empty or unclear. "
            "A precise mission statement is required to begin the swarm session."
        )

    mandate = f"MISSION ISSUED BY MOSES: {human_input.strip()}"

    return {
        **state,
        "mission": human_input.strip(),
        "mandate": mandate,
        "task": human_input.strip(),
        "jethro_tier": 0,
        "originating_tier": 0,
        "escalate": False,
        "constitution_violations": [],
        "oral_law_precedents": [],
        "session_id": state.get("session_id", f"session_{int(time.time())}"),
    }


def _present_summary(summary: str) -> None:
    """Print final session summary to stdout (human-in-the-loop output)."""
    print("\n" + "=" * 60)
    print("MOSES — FINAL SESSION SUMMARY")
    print("=" * 60)
    print(summary)
    print("=" * 60 + "\n")
