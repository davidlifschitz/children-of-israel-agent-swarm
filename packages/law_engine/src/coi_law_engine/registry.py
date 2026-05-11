from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class LawRegistry:
    constitution: dict[str, Any]
    commandments: dict[str, Any]
    oral_law: dict[str, Any]
    mission_config: dict[str, Any]

    @classmethod
    def from_repo_root(cls, repo_root: str | Path) -> "LawRegistry":
        root = Path(repo_root)
        return cls(
            constitution=_load_yaml(root / "law" / "constitution.yaml"),
            commandments=_load_yaml(root / "law" / "commandments.yaml"),
            oral_law=_load_yaml(root / "law" / "oral_law.yaml"),
            mission_config=_load_yaml(root / "config" / "mission.yaml"),
        )

    @property
    def hard_commandments(self) -> list[dict[str, Any]]:
        return list((self.constitution.get("constitution") or {}).get("commandments") or [])

    @property
    def oral_rule_ids(self) -> set[str]:
        return {str(rule.get("id")) for rule in self.oral_law.get("meta_rules", [])}

    @property
    def directive_count(self) -> int:
        total = 0
        for theme in self.commandments.get("themes", []):
            for subcategory in theme.get("subcategories", []):
                total += len(subcategory.get("directives", []))
        return total


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required law/config artifact is missing: {path}")
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data

