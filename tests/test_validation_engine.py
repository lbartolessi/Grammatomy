import sys
from pathlib import Path

import pytest
import yaml

# Ensure src/core is in path
sys.path.append(str(Path(__file__).parents[1] / "src" / "core"))

from grammatomy.validation_engine import ValidationEngine

# Mock Rules Data for Testing
# We define a controlled environment to test logic without relying on the production YAML
MOCK_RULES = {
    "tree_config": {
        "language": "es",
        "standard": "Mock Standard",
        "description": "Mock rules for testing",
        "version": "1.0",
    },
    "nodes": [
        {
            "id": "ROOT",
            "allowed_children": {"mandatory": [], "optional": ["S"]},
            "allowed_parents": [],
            "description": "Root",
        },
        {
            "id": "S",
            "allowed_children": {
                "mandatory": ["VP"],
                "optional": ["NP", "HybridNode"],
            },
            "allowed_parents": ["ROOT"],
            "description": "Sentence",
        },
        {
            "id": "NP",
            "allowed_children": {"mandatory": ["N"], "optional": ["DET"]},
            "allowed_parents": ["S", "VP"],
            "description": "Noun Phrase",
        },
        {
            "id": "VP",
            "allowed_children": {"mandatory": ["V"], "optional": ["NP"]},
            "allowed_parents": ["S"],
            "description": "Verb Phrase",
        },
        {
            "id": "HybridNode",
            "allowed_children": {"mandatory": [], "optional": ["N"]},
            "allowed_parents": ["S"],
            "description": "Test Node for Overlap",
        },
        {
            "id": "DET",
            "allowed_children": {"mandatory": [], "optional": []},
            "allowed_parents": ["NP"],
            "description": "Determiner",
        },
        {
            "id": "N",
            "allowed_children": {"mandatory": [], "optional": []},
            "allowed_parents": ["NP", "HybridNode"],
            "description": "Noun",
        },
        {
            "id": "V",
            "allowed_children": {"mandatory": [], "optional": []},
            "allowed_parents": ["VP"],
            "description": "Verb",
        },
    ],
}


@pytest.fixture
def validation_engine(tmp_path):
    """Creates a ValidationEngine instance with mock rules."""
    rules_file = tmp_path / "test_rules.yaml"
    with open(rules_file, "w", encoding="utf-8") as f:
        yaml.dump(MOCK_RULES, f)

    # Initialize engine with unique path
    return ValidationEngine(str(rules_file), "es")


def test_initialization(validation_engine):
    """Test that rules are loaded and reverse index is built."""
    assert "S" in validation_engine.rules
    assert "NP" in validation_engine.allowed_children
    # Check reverse index construction (Child -> Valid Parents)
    assert "NP" in validation_engine._reverse_index["DET"]
    assert "HybridNode" in validation_engine._reverse_index["N"]
    assert "S" in validation_engine._reverse_index["VP"]


def test_can_add_child(validation_engine):
    """Test simple parent-child compatibility."""
    # Valid
    allowed, _ = validation_engine.can_add_child("S", "NP")
    assert allowed is True

    # Invalid (Parent doesn't allow)
    allowed, reason = validation_engine.can_add_child("S", "DET")
    assert allowed is False
    assert "does not allow" in reason


def test_can_convert_node_logic(validation_engine):
    """Test the A intersection B logic for dropdown population."""

    # Scenario 1: NP containing [DET, N] inside S
    # Parent S allows: {NP, VP, HybridNode}
    # Child DET allows parents: {NP}
    # Child N allows parents: {NP, HybridNode}
    # Intersection(Children) = {NP}
    # Intersection(Parent) = {NP}
    # Result must be exactly ["NP"]
    valid_tags = validation_engine.can_convert_node(
        current_tag="NP", ancestor_tags=["S"], current_children_tags=["DET", "N"]
    )
    assert valid_tags == ["NP"]

    # Scenario 2: NP containing only [N] inside S
    # Parent S allows: {NP, VP, HybridNode}
    # Child N allows parents: {NP, HybridNode}
    # Intersection(Children) = {NP, HybridNode}
    # Intersection(Parent) = {NP, HybridNode}
    # Result must be ["HybridNode", "NP"]
    valid_tags = validation_engine.can_convert_node(
        current_tag="NP", ancestor_tags=["S"], current_children_tags=["N"]
    )
    assert sorted(valid_tags) == ["HybridNode", "NP"]

    # Scenario 3: VP containing [V] inside S
    # Child V allows parents: {VP}
    # Result must be ["VP"]
    valid_tags = validation_engine.can_convert_node(
        current_tag="VP", ancestor_tags=["S"], current_children_tags=["V"]
    )
    assert valid_tags == ["VP"]


def test_validate_structure_mandatory(validation_engine):
    """Test mandatory children validation."""
    # S requires VP (somewhere in descendants)
    valid, _ = validation_engine.validate_requirements("S", ["NP", "VP"])
    assert valid is True

    valid, msg = validation_engine.validate_requirements("S", ["NP"])
    assert valid is False
    assert "Missing required structure" in msg


def test_can_delete_child(validation_engine):
    """Test deletion protection for mandatory children."""
    # Case 1: Deleting the only VP from S (Illegal)
    allowed, msg = validation_engine.can_delete_child("S", "VP", sibling_tags=["NP"])
    assert allowed is False
    assert "mandatory" in msg

    # Case 2: Deleting one VP when another exists (Legal)
    allowed, _ = validation_engine.can_delete_child(
        "S", "VP", sibling_tags=["NP", "VP"]
    )
    assert allowed is True
