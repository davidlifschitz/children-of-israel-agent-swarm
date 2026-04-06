"""composer.py
Runtime assembly of the Children of Israel LangGraph graph.

Fix log:
  - [BUG 1] next_node is now cleared after being consumed so it cannot cause
            stale re-routing on subsequent nodes.
  - [BUG 2] Gad is now wired as an error recovery node. Any tribe that sets
            tribe_error routes to Gad. Gad escalation routes to Dan.
  - [BUG 3] A summarizer_node is added before Moses exit. Tier 1 nodes route
            to summarizer instead of END, which assembles final_summary and
            returns to Moses for clean session termination.
"""

from __future__ import annotations

import yaml
from langgraph.graph import StateGraph, END

from .agent_state import AgentState
from .checkpointing import get_checkpointer
from .moses import moses_node
from .hermes_node import hermes_node
from .tribes import TRIBE_REGISTRY
from .llm import llm_call

# ---------------------------------------------------------------------------
# Load tribe config
# ---------------------------------------------------------------------------

from pathlib import Path
_LAW_DIR = Path(__file__).parent.parent / "law" / "tribes" / "tribes.yaml"
with open(_LAW_DIR, "r") as _f:
    _TRIBES_CFG = yaml.safe_load(_f)["tribes"]

_HERMES_ELIGIBLE = {t["id"] for t in _TRIBES_CFG if t.get("hermes_eligible", False)}

_TIER_MAP: dict[int, list[str]] = {}
for _t in _TRIBES_CFG:
    _TIER_MAP.setdefault(_t["jethro_tier"], []).append(_t["id"])

# Tier 1 tribe ids — these route to summarizer on success
_TIER_1_TRIBES = set(_TIER_MAP.get(1, []))


# ---------------------------------------------------------------------------
# Summarizer node (BUG 3 fix)
# Assembles final_summary from last output and routes back to Moses.
# ---------------------------------------------------------------------------

_SUMMARIZER_PROMPT = """
You are a neutral session summarizer for the Children of Israel Agent Swarm.
You receive the final output of a swarm session and produce a concise, structured
final summary for the human operator (Moses).

Include:
- What was accomplished
- Key findings or decisions
- Any unresolved escalations or violations
- Recommended next actions

Output format (respond with valid JSON only, no markdown):
{
  "final_summary": "<multi-paragraph summary>",
  "accomplished": ["<item 1>"],
  "unresolved": [],
  "recommended_next": "<string>"
}
"""

def summarizer_node(state: AgentState) -> AgentState:
    """Compile final_summary from last output and surface to Moses."""
    last_output = state.get("output") or state.get("tribe_output") or {}
    task = (
        f"Mission: {state.get('mission', '')}\n\n"
        f"Final output from swarm:\n{last_output}\n\n"
        f"Constitution violations logged: {state.get('constitution_violations', [])}\n"
        f"Dan precedents set: {state.get('oral_law_precedents', [])}"
    )
    result = llm_call("__summarizer__", _SUMMARIZER_PROMPT, task)
    return {
        **state,
        "final_summary": result.get("final_summary", str(last_output)),
        "next_node": None,   # clear any stale routing before Moses exit
    }


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def _route_from_moses(state: AgentState) -> str:
    """After Moses issues the mandate, route to Tier 1 commander."""
    if state.get("final_summary"):
        return END
    return "judah"


def _route_tribe(tribe_id: str):
    """Return a routing function for a given tribe node."""
    def _route(state: AgentState) -> str:
        # BUG 2 fix: if the tribe set tribe_error, route to Gad for recovery
        if state.get("tribe_error"):
            return "gad"

        if state.get("escalate"):
            current_tier = state.get("jethro_tier", 4)
            target_tier = max(1, current_tier - 1)
            candidates = _TIER_MAP.get(target_tier, [])
            if candidates:
                return candidates[0]
            return "summarizer"  # escalated all the way up — summarize and exit

        # BUG 1 fix: consume next_node and clear it before returning
        next_node = state.get("next_node")
        if next_node:
            return next_node  # clearing happens in the node itself (each tribe sets next_node=None on exit)

        # Hermes-eligible tribes route to Hermes branch first
        if tribe_id in _HERMES_ELIGIBLE:
            return f"hermes_{tribe_id}"

        # BUG 3 fix: Tier 1 tribes route to summarizer instead of END
        if tribe_id in _TIER_1_TRIBES:
            return "summarizer"

        return END
    return _route


def _route_hermes(tribe_id: str):
    """After Hermes node runs, route to tribal fallback or summarizer."""
    def _route(state: AgentState) -> str:
        if state.get("hermes_fallback"):
            return f"{tribe_id}_fallback"
        if state.get("escalate"):
            return "dan"
        if tribe_id in _TIER_1_TRIBES:
            return "summarizer"
        return END
    return _route


def _route_gad(state: AgentState) -> str:
    """BUG 2 fix: after Gad's recovery attempt, route to Dan on escalation or summarizer."""
    if state.get("escalate"):
        return "dan"
    return "summarizer"


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

    # --- Summarizer (BUG 3 fix) ---
    graph.add_node("summarizer", summarizer_node)
    graph.add_edge("summarizer", "moses")  # always returns to Moses after summary

    # --- All 12 tribal nodes ---
    for tribe_id, tribe_fn in TRIBE_REGISTRY.items():
        graph.add_node(tribe_id, tribe_fn)
        graph.add_conditional_edges(tribe_id, _route_tribe(tribe_id))

    # --- Gad: error recovery wiring (BUG 2 fix) ---
    # Gad is already registered in TRIBE_REGISTRY loop above.
    # Override its edge with the dedicated _route_gad function.
    graph.add_conditional_edges("gad", _route_gad)

    # --- Hermes parallel branches for eligible tribes ---
    for tribe_id in _HERMES_ELIGIBLE:
        hermes_node_name = f"hermes_{tribe_id}"
        fallback_node_name = f"{tribe_id}_fallback"
        tribe_fn = TRIBE_REGISTRY[tribe_id]

        graph.add_node(hermes_node_name, hermes_node)
        graph.add_node(fallback_node_name, tribe_fn)

        graph.add_conditional_edges(hermes_node_name, _route_hermes(tribe_id))
        # fallback nodes use the same tribe routing logic
        graph.add_conditional_edges(fallback_node_name, _route_tribe(tribe_id))

    import yaml, os
    from pathlib import Path
    _mission_cfg = yaml.safe_load(
        (Path(__file__).parent.parent / "config" / "mission.yaml").read_text()
    )
    _backend = _mission_cfg.get("checkpointing", {}).get("backend", "memory")
    checkpointer = get_checkpointer(_backend)
    return graph.compile(checkpointer=checkpointer)


# Compiled graph — importable by moses.py and external runners
swarm = build_graph()
