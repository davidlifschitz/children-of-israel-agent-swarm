from __future__ import annotations

import ast
from pathlib import Path


PACKAGE_ROOTS = {
    "coi_contracts": Path("packages/contracts/src/coi_contracts"),
    "coi_runtime": Path("packages/runtime/src/coi_runtime"),
    "coi_law_engine": Path("packages/law_engine/src/coi_law_engine"),
    "coi_storage": Path("packages/storage/src/coi_storage"),
    "coi_orchestrator": Path("packages/orchestrator/src/coi_orchestrator"),
    "coi_api": Path("packages/api/src/coi_api"),
    "coi_integrations": Path("packages/integrations/src/coi_integrations"),
}

ALLOWED_IMPORTS = {
    "coi_contracts": set(),
    "coi_runtime": {"coi_contracts"},
    "coi_law_engine": {"coi_contracts"},
    "coi_storage": {"coi_contracts"},
    "coi_orchestrator": {"coi_contracts", "coi_runtime", "coi_law_engine", "coi_storage"},
    "coi_api": {"coi_contracts", "coi_orchestrator"},
    "coi_integrations": {"coi_orchestrator"},
}


def main() -> int:
    violations: list[str] = []
    for package, root in PACKAGE_ROOTS.items():
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                for imported in _imported_roots(node):
                    if imported in PACKAGE_ROOTS and imported != package:
                        if imported not in ALLOWED_IMPORTS[package]:
                            violations.append(f"{path}: {package} cannot import {imported}")
    if violations:
        print("\n".join(violations))
        return 1
    print("OK - import boundaries hold")
    return 0


def _imported_roots(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module.split(".")[0]]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
