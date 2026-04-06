"""constitution_enforcer.py
Runtime enforcement of the Ten Commandments (Universal Agent Constitution).
Layer 1 of 3 in the Children of Israel Agent Swarm Law Architecture.

Applied as pre/post execution middleware on every tribal node.
Violations are logged to state["constitution_violations"].
Hard-stop violations (C2, C3, C8) also set state["tribe_error"].
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import yaml


class ConstitutionEnforcer:
    """Runtime enforcer for the Ten Commandments constitution.

    Loaded once at import time as a module-level singleton.
    Call enforce(state, output) after each tribal LLM call.
    """

    def __init__(self) -> None:
        constitution_path = Path(__file__).parent.parent / "law" / "constitution.yaml"
        with constitution_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        # Keyed by commandment id (int) for fast lookup
        self.commandments: dict[int, dict] = {
            c["id"]: c for c in data["constitution"]["commandments"]
        }

    # ------------------------------------------------------------------
    # Pre-execution checks (run BEFORE the tribe's LLM call)
    # ------------------------------------------------------------------

    def check_pre_execution(self, state: dict) -> list[str]:
        """Return a list of violation strings found in state before execution.

        An empty list means no violations detected.
        """
        violations: list[str] = []

        # C3: mandate must be present and non-empty
        if not state.get("mandate"):
            violations.append(
                "C3: No mandate — agent must not act without explicit mandate"
            )

        # C4: jethro_tier must be assigned
        if state.get("jethro_tier") is None:
            violations.append(
                "C4: No tier assigned — hierarchy must be honored"
            )

        # C8: task must not contain scope-breach keywords
        task: str = state.get("task") or ""
        scope_breach_keywords = [
            "override",
            "bypass",
            "ignore all",
            "disregard",
            "jailbreak",
        ]
        if any(kw in task.lower() for kw in scope_breach_keywords):
            violations.append(
                "C8: Scope breach detected — agent must know its limits"
            )

        return violations

    # ------------------------------------------------------------------
    # Post-execution checks (run AFTER the tribe's LLM call on output)
    # ------------------------------------------------------------------

    def check_post_execution(self, state: dict, output: Any) -> list[str]:
        """Return a list of violation strings found in output after execution.

        An empty list means no violations detected.
        """
        violations: list[str] = []

        # C2: fabrication markers in any string value of the output dict
        fabrication_phrases = [
            "i fabricated",
            "i made this up",
            "this is not real",
            "i'm not sure but i'll say",
        ]
        if isinstance(output, dict):
            for value in output.values():
                if isinstance(value, str) and any(
                    phrase in value.lower() for phrase in fabrication_phrases
                ):
                    violations.append(
                        "C2: Fabrication detected — thou shalt not fabricate"
                    )
                    break  # one violation per check is sufficient

        # C5: output must be a non-empty dict
        if not isinstance(output, dict) or len(output) == 0:
            violations.append(
                "C5: Unstructured output — communicate with clarity"
            )

        # C7: output must be JSON-serializable
        try:
            json.dumps(output)
        except TypeError:
            violations.append(
                "C7: Non-serializable output — preserve integrity of information"
            )

        return violations

    # ------------------------------------------------------------------
    # Main enforcement entry point
    # ------------------------------------------------------------------

    def enforce(self, state: dict, output: Any) -> tuple[dict, list[str]]:
        """Run all pre- and post-execution checks and update state in place.

        Returns:
            (updated_state, all_violations)  — all_violations may be empty.

        Side-effects on state:
            state["constitution_violations"] is extended with any new violations.
            state["tribe_error"] is set to the first hard-stop violation (C2/C3/C8)
            if one is present.
        """
        pre_violations = self.check_pre_execution(state)
        post_violations = self.check_post_execution(state, output)
        all_violations = pre_violations + post_violations

        # Merge into cumulative violation log
        state["constitution_violations"] = (
            state.get("constitution_violations") or []
        ) + all_violations

        # Hard stops: C2, C3, C8 — set tribe_error to first offending violation
        hard_stop_prefixes = ("C2:", "C3:", "C8:")
        for violation in all_violations:
            if violation.startswith(hard_stop_prefixes):
                state["tribe_error"] = violation
                break

        return state, all_violations


# ---------------------------------------------------------------------------
# Singleton — import this instance in tribe files
# ---------------------------------------------------------------------------
enforcer = ConstitutionEnforcer()
