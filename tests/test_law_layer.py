"""test_law_layer.py — Tests that the law layer YAML files are valid and complete."""
import pytest
import yaml
from pathlib import Path

LAW_DIR = Path(__file__).parent.parent / "law"


# ---------------------------------------------------------------------------
# constitution.yaml
# ---------------------------------------------------------------------------

def test_constitution_has_10_commandments():
    """The constitution must have exactly 10 commandments."""
    with (LAW_DIR / "constitution.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    commandments = data["constitution"]["commandments"]
    assert len(commandments) == 10, (
        f"Expected 10 commandments, got {len(commandments)}"
    )


def test_constitution_commandments_have_required_fields():
    """Each commandment must carry id, name, and directive."""
    with (LAW_DIR / "constitution.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    commandments = data["constitution"]["commandments"]
    for c in commandments:
        assert "id" in c, f"Commandment missing 'id': {c}"
        assert "name" in c, f"Commandment {c.get('id')} missing 'name'"
        # The field is 'directive' in constitution.yaml
        assert "directive" in c, (
            f"Commandment {c.get('id')} missing 'directive'"
        )


# ---------------------------------------------------------------------------
# commandments.yaml (613 granular directives)
# ---------------------------------------------------------------------------

def test_commandments_has_six_themes():
    """commandments.yaml must ultimately define exactly 6 themes."""
    with (LAW_DIR / "commandments.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert len(data["themes"]) == 6, (
        f"Expected 6 themes, got {len(data['themes'])}"
    )


def test_each_theme_has_directives():
    """Every theme must have subcategories and at least 10 total directives."""
    with (LAW_DIR / "commandments.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    for theme in data["themes"]:
        assert len(theme["subcategories"]) > 0, (
            f"Theme {theme['id']} has no subcategories"
        )
        total_directives = sum(
            len(sc.get("directives", [])) for sc in theme["subcategories"]
        )
        assert total_directives >= 10, (
            f"Theme {theme['id']} has only {total_directives} directives (need >= 10)"
        )


# ---------------------------------------------------------------------------
# oral_law.yaml
# ---------------------------------------------------------------------------

def test_oral_law_has_four_rules():
    """oral_law.yaml must define exactly 4 meta-rules."""
    with (LAW_DIR / "oral_law.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert len(data["meta_rules"]) == 4, (
        f"Expected 4 meta-rules, got {len(data['meta_rules'])}"
    )


def test_oral_law_rule_ids():
    """All 4 Oral Law rules must have IDs OL-001 through OL-004."""
    with (LAW_DIR / "oral_law.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    ids = {rule["id"] for rule in data["meta_rules"]}
    expected = {"OL-001", "OL-002", "OL-003", "OL-004"}
    assert ids == expected, f"Oral Law rule IDs mismatch: {ids}"
