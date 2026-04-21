from __future__ import annotations

from typing import Any, Dict, Tuple

REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "task_id",
    "task_type",
    "routing",
    "payload",
]


def validate_bootstrap_task(task: Dict[str, Any]) -> Tuple[bool, list[str]]:
    errors: list[str] = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in task:
            errors.append(f"Missing required field: {field}")

    if task.get("task_type") != "repo.bootstrap":
        errors.append("Expected task_type to equal 'repo.bootstrap'")

    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    routing = task.get("routing") if isinstance(task.get("routing"), dict) else {}

    if not payload.get("project_name"):
        errors.append("payload.project_name is required")
    if not payload.get("project_role"):
        errors.append("payload.project_role is required")
    if routing.get("target_project") != "spec-to-repo":
        errors.append("routing.target_project must point to spec-to-repo")

    return (len(errors) == 0, errors)
