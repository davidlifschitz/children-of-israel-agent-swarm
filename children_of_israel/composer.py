"""composer.py
Runtime assembly of the Children of Israel LangGraph graph.

Responsibilities:
  - Build the full StateGraph from tribal nodes + Hermes parallel branch
  - Route tasks to the correct Jethro tier node
  - Wire the Hermes parallel branch for hermes_eligible tribes
  - Handle escalation routing up the hierarchy
  - Connect Moses as root entry and exit point

Hermes Routing Logic:
  For hermes_eligible tribes (Reuben, Naphtali, Asher), the composer adds
  a parallel Hermes branch. On success, Hermes output is used. On
  hermes_fallback=True, the original tribal node handles the task.
"""

from __future__ import annotations

import yaml
from langgraph.graph import StateGraph, END

from .agent_state import AgentState
from .moses import moses_node
from .hermes_node import hermes_node
from .tribes import TRIBE_REGISTRY

# Load tribe config to determine hermes_eligible tribes at build time
with open("law/tribes/tribes.yaml", "r") as _f:
    _TRIBES_CFG = yaml.safe_load(_f)["tribes"]

_HERMES_ELIGIBLE = {t["id"] for t in _TRIBES_CFG if t.get("hermes_eligible", False)}

# Jethro tier -> list of tribe ids at that tier
_TIER_MAP: dict[int, list[str]] = {}
for _t in _TRIBES_CFG:
    _TIER_MAP.setdefault(_t["jethro_tier"], []).append(_t["id"])


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def _route_from_moses(state: AgentState) -> str:
    """After Moses issues the mandate, route to Tier 1 commander."""
    if state.get("final_summary"):
        return END
    # Default entry: Judah as primary Tier 1 commander
    return "judah"


def _route_tribe(tribe_id: str):
    """Return a routing function for a given tribe node."""
    def _route(state: AgentState) -> str:
        if state.get("escalate"):
            # Escalate up one tier via OL-003 (proportional escalation)
            current_tier = state.get("jethro_tier", 4)
            target_tier = max(1, current_tier - 1)
            candidates = _TIER_MAP.get(target_tier, [])
            if candidates:
                return candidates[0]  # first judge at the target tier handles it
            return "moses"  # bubble all the way up if no tier found

        if state.get("next_node"):
            return state["next_node"]

        # Hermes-eligible tribes: route to Hermes first, fallback handled after
        if tribe_id in _HERMES_ELIGIBLE:
            return f"hermes_{tribe_id}"

        return END
    return _route


def _route_hermes(tribe_id: str):
    """After Hermes node runs, route to tribal fallback or END."""
    def _route(state: AgentState) -> str:
        if state.get("hermes_fallback"):
            # Hermes failed - fall back to the original tribal node
            return f"{tribe_id}_fallback"
        if state.get("escalate"):
            return "dan"  # escalate to Dan (Tier 1 judge) for constitution violations
        return END
    return _route


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Assemble and return the compiled Children of Israel LangGraph graph."""
    graph = StateGraph(AgentState)

    # --- Moses (root) ---
    graph.add_node("moses", moses_node)
    graph.set_entry_point("moses")
    graph.add_conditional_edges("moses", _route_from_moses)

    # --- All 12 tribal nodes ---
    for tribe_id, tribe_fn in TRIBE_REGISTRY.items():
        graph.add_node(tribe_id, tribe_fn)
        graph.add_conditional_edges(tribe_id, _route_tribe(tribe_id))

    # --- Hermes parallel branches for eligible tribes ---
    # Each eligible tribe gets:
    #   1. A hermes_{tribe_id} node (the Hermes executor)
    #   2. A {tribe_id}_fallback node (the original tribal node, re-used)
    for tribe_id in _HERMES_ELIGIBLE:
        hermes_node_name = f"hermes_{tribe_id}"
        fallback_node_name = f"{tribe_id}_fallback"
        tribe_fn = TRIBE_REGISTRY[tribe_id]

        graph.add_node(hermes_node_name, hermes_node)
        graph.add_node(fallback_node_name, tribe_fn)

        graph.add_conditional_edges(hermes_node_name, _route_hermes(tribe_id))
        graph.add_edge(fallback_node_name, END)

    return graph.compile()


# Compiled graph — importable by moses.py and external runners
swarm = build_graph()
