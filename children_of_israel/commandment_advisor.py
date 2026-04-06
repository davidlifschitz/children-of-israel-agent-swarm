"""commandment_advisor.py
Loads per-tribe behavioral directives from the 613 Commandments.
Used to inject relevant commandments into each tribe's system prompt.
"""
from __future__ import annotations
import yaml
from pathlib import Path


class CommandmentAdvisor:
    """Builds a per-tribe index of relevant directives from commandments.yaml."""

    def __init__(self) -> None:
        path = Path(__file__).parent.parent / "law" / "commandments.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        # Build index: lowercase_tribe_name -> list of directives
        self._index: dict[str, list[dict]] = {}
        for theme in data.get("themes", []):
            for subcategory in theme.get("subcategories", []):
                for directive in subcategory.get("directives", []):
                    for tribe_name in directive.get("tribe_affinity", []):
                        key = tribe_name.lower()
                        self._index.setdefault(key, []).append(directive)

    def get_directives_for_tribe(self, tribe_id: str) -> list[dict]:
        """Return all directives where tribe_affinity includes this tribe."""
        return self._index.get(tribe_id.lower(), [])

    def format_for_prompt(self, directives: list[dict]) -> str:
        """Format directives as a compact numbered list for prompt injection."""
        if not directives:
            return ""
        lines = ["--- Applicable Commandments ---"]
        for i, d in enumerate(directives[:20], 1):  # cap at 20 to avoid prompt bloat
            snippet = d.get("directive", "")[:100]
            lines.append(f"{i}. [{d['id']}] {d['name']}: {snippet}...")
        lines.append("--- End Commandments ---")
        return "\n".join(lines)


# Module-level singleton
advisor = CommandmentAdvisor()
