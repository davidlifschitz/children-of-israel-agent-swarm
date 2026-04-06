"""oral_law_engine.py
Executable implementation of the Oral Law meta-rules (OL-001 to OL-004).
Layer 3 of 3 in the Children of Israel Agent Swarm Law Architecture.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from children_of_israel.precedent_store import PrecedentStore

if TYPE_CHECKING:
    from children_of_israel.agent_state import AgentState

# Tier 1 tribes authorised to invoke OL-001 context suspension
_TIER_1_TRIBES: list[str] = ["judah", "joseph", "dan", "levi"]

# Escalation targets defined by OL-003
_ESCALATION_MAP: dict[str, str] = {
    "minor": "issachar",    # Tier 3 handles minor conflicts
    "major": "dan",          # Tier 1 judge handles major conflicts
    "critical": "judah",     # Senior Tier 1 commander handles critical conflicts
}

# SLA threshold for OL-004 (seconds)
_MOSES_SLA_SECONDS: float = 300.0


class OralLawEngine:
    """Executes the four Oral Law meta-rules (OL-001 to OL-004)."""

    # ------------------------------------------------------------------
    # OL-001: Context Over Code
    # ------------------------------------------------------------------
    def apply_context_over_code(
        self,
        state: "AgentState",
        directive_id: str,
        judge_tribe_id: str,
    ) -> bool:
        """OL-001: A Tier 1 judge can suspend a directive for this instance.

        Args:
            state: The shared AgentState dict.
            directive_id: Identifier of the directive to suspend.
            judge_tribe_id: The tribe ID of the judge invoking suspension.

        Returns:
            True if the suspension was applied, False otherwise.
        """
        if judge_tribe_id not in _TIER_1_TRIBES:
            return False

        note = (
            f"OL-001: Directive {directive_id} suspended by "
            f"{judge_tribe_id} for this instance"
        )
        violations: list[str] = state.get("constitution_violations") or []
        violations.append(note)
        state["constitution_violations"] = violations
        return True

    # ------------------------------------------------------------------
    # OL-002: The Dan Precedent
    # ------------------------------------------------------------------
    def log_precedent(
        self,
        state: "AgentState",
        conflict_type: str,
        ruling_summary: str,
    ) -> str:
        """OL-002: Log Dan's ruling as a precedent for future conflicts.

        Args:
            state: The shared AgentState dict.
            conflict_type: Category/type of the conflict being ruled on.
            ruling_summary: Human-readable summary of Dan's ruling.

        Returns:
            The generated precedent ID string.
        """
        precedent_id = (
            f"DAN-{conflict_type.upper().replace(' ', '_')}-{int(time.time())}"
        )

        precedents: list[str] = state.get("oral_law_precedents") or []
        precedents.append(precedent_id)
        state["oral_law_precedents"] = precedents

        PrecedentStore().write(
            {
                "id": precedent_id,
                "conflict_type": conflict_type,
                "ruling": ruling_summary,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return precedent_id

    # ------------------------------------------------------------------
    # OL-003: Proportional Escalation
    # ------------------------------------------------------------------
    def resolve_proportional_escalation(
        self,
        state: "AgentState",
        conflict_impact: str,
    ) -> str:
        """OL-003: Return the appropriate escalation target based on impact.

        Args:
            state: The shared AgentState dict.
            conflict_impact: One of "minor", "major", or "critical".

        Returns:
            Tribe ID of the node that should handle this conflict.
        """
        # Unknown impact levels default to "dan" (the judge)
        return _ESCALATION_MAP.get(conflict_impact, "dan")

    # ------------------------------------------------------------------
    # OL-004: The Silence of Moses
    # ------------------------------------------------------------------
    def apply_moses_silence_fallback(
        self,
        state: "AgentState",
        elapsed_seconds: float,
    ) -> dict:
        """OL-004: If Moses SLA (300 s) elapsed without a ruling, act conservatively.

        Args:
            state: The shared AgentState dict.
            elapsed_seconds: Seconds since the conflict reached Moses.

        Returns:
            A dict describing the action to take.
        """
        if elapsed_seconds > _MOSES_SLA_SECONDS:
            return {
                "action": "conservative_hold",
                "rationale": (
                    "Moses SLA exceeded — defaulting to Theme 5 "
                    "(Integrity & Purity) conservative action"
                ),
                "defer_to": "levi",
                "escalate": True,
            }
        return {
            "action": "await",
            "rationale": "Moses SLA not yet exceeded",
            "elapsed": elapsed_seconds,
        }


# Module-level singleton
oral_law_engine = OralLawEngine()
