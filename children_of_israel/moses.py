"""moses.py
Root human-in-the-loop LangGraph node.

Moses is Tier 0 (Root) in the Jethro hierarchy. His responsibilities:
  - Receive the human mission statement
  - Validate the mission is non-empty and clear (Commandment 5)
  - Issue the mandate into AgentState
  - Receive the final_summary (written by summarizer_node) and present it
  - Enforce OL-004 (Silence of Moses): if no ruling is issued within SLA,
    default to most conservative action

BUG 3 fix:
  Moses no longer assembles final_summary itself. summarizer_node (in
  composer.py) writes final_summary before routing back here. Moses's
  session-end path simply reads and presents it.
"""

from __future__ import annotations

import time
from typing import Optional

from .agent_state import AgentState

_MOSES_SLA_SECONDS = 300


def moses_node(state: AgentState) -> AgentState:
    """Moses root node. Entry point and exit point of every swarm session."""
    human_input: Optional[str] = state.get("human_input")

    # --- Session end path ---
    # summarizer_node writes final_summary before routing back here.
    # Moses presents it and signals END via next_node=None + final_summary set.
    final_summary = state.get("final_summary")
    if final_summary:
        _present_summary(final_summary)
        # Return state unchanged — composer _route_from_moses sees final_summary
        # and routes to END.
        return {
            **state,
            "next_node": None,   # BUG 1 guard: ensure no stale routing leaks out
        }

    # --- Session start path ---
    if not human_input or not human_input.strip():
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
        "next_node": None,              # BUG 1 guard: start clean
        "tribe_error": None,            # BUG 2 guard: start clean
        "hermes_error": None,
        "hermes_fallback": False,
        "final_summary": None,          # BUG 3 guard: ensure summarizer writes this fresh
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
