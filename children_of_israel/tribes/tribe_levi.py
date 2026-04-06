"""tribe_levi.py — Levi: Priest / Steward
Tier 1 senior (cross-tier). Domain: Memory, system integrity, record-keeping.
Hermes eligible: no

BUG 1 fix: sets next_node=None on exit.
"""

from __future__ import annotations
from ..agent_state import AgentState
from ..llm import llm_call
from children_of_israel.constitution_enforcer import enforcer

SYSTEM_PROMPT = """
You are Levi, the Priest and Steward of the Children of Israel swarm.
Your domain is memory, system integrity, and sacred record-keeping.

Persona:
- Meticulous and devoted. You are the keeper of all that has happened.
- Cross-tier: you serve all tiers simultaneously as memory custodian.
- Your shadow trait is gatekeeping — you must not become an access bottleneck.

You will receive a state snapshot or record to archive. Summarize and store it faithfully.

Mandatory behaviors:
- [C7] All records must be bit-for-bit faithful. No lossy compression of facts.
- [C2] Never reconstruct or infer missing records. Mark gaps explicitly as UNKNOWN.
- [C4] Your records are accessible on demand by any tier.

Output format (respond with valid JSON only, no markdown):
{
  "tribe": "levi",
  "output_type": "memory_record",
  "records": ["<record 1>", "<record 2>"],
  "gaps": [],
  "integrity_status": "ok",
  "escalate": false
}
"""


def levi_node(state: AgentState) -> AgentState:
    task = str(state.get("output") or state.get("task", ""))
    try:
        result = llm_call("levi", SYSTEM_PROMPT, task)
        try:
            state, _ = enforcer.enforce(state, result)
        except Exception:
            pass  # constitution enforcement failure must not crash the tribe

        # --- Write immutable audit record (OL-002: Levi is the record-keeper) ---
        try:
            import json
            from datetime import datetime
            from pathlib import Path

            audit_dir = Path(__file__).parent.parent.parent / "data"
            audit_dir.mkdir(parents=True, exist_ok=True)
            audit_log_path = audit_dir / "audit_log.jsonl"

            final_summary_preview = str(state.get("final_summary", ""))[:200]
            audit_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": state.get("session_id", "unknown"),
                "mission": state.get("mission", ""),
                "constitution_violations": state.get("constitution_violations", []),
                "oral_law_precedents": state.get("oral_law_precedents", []),
                "final_summary_preview": final_summary_preview,
                "simeon_severity": state.get("tribe_output", {}).get("severity", "unknown") if isinstance(state.get("tribe_output"), dict) else "unknown",
            }

            with audit_log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(audit_record) + "\n")
        except Exception:
            pass  # Record-keeping failure must not crash Levi's node

        return {
            **state,
            "current_tribe": "levi",
            "jethro_tier": 1,
            "tribe_output": result,
            "output": result,
            "next_node": None,
            "tribe_error": None,
            "escalate": bool(result.get("escalate", False)),
        }
    except Exception as exc:
        return {**state, "current_tribe": "levi", "tribe_error": str(exc), "next_node": None}
