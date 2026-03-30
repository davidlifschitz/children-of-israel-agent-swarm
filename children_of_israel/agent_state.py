"""agent_state.py
Typed AgentState schema shared across all nodes in the swarm.
All LangGraph nodes read from and write to this schema.
"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # --- Mission & mandate ---
    mission: str                    # top-level mission string issued by Moses
    mandate: str                    # explicit task mandate for the current node (required by Commandment 3)
    task: str                       # concrete task string passed to the active node

    # --- Routing ---
    current_tribe: str              # id of the tribe currently handling the task
    next_node: Optional[str]        # explicit next node override (used by escalation paths)
    escalate: bool                  # if True, composer routes task up the Jethro hierarchy
    escalation_reason: str          # human-readable reason for escalation

    # --- Tribe output ---
    output: Any                     # final output from the active node (tribal or Hermes)
    tribe_output: Any               # raw output from the tribal LangGraph node
    tribe_error: Optional[str]      # error string if tribal node failed

    # --- Hermes pipeline ---
    hermes_output: Any              # parsed JSON output from Hermes node
    hermes_fallback: bool           # True = Hermes failed, fall back to tribal node
    hermes_error: Optional[str]     # error string from Hermes node

    # --- Jethro hierarchy metadata ---
    jethro_tier: int                # tier of the current active node (1-4)
    originating_tier: int           # tier where the task originated
    session_id: str                 # unique session identifier for checkpointing

    # --- Law layer ---
    constitution_violations: list[str]   # log of any commandment violations encountered
    oral_law_precedents: list[str]       # Dan precedent IDs applied this session (OL-002)

    # --- Moses (root) ---
    human_input: Optional[str]      # raw human input at the Moses node
    final_summary: Optional[str]    # final summary returned to Moses at session end
