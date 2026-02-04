"""
Validation Module for Grammatomy.

Implements the core validation logic for the syntax tree:
1. Safety (Ghost Nodes): Strict checks for incomplete editing.
2. Structural Integrity (Metasyntax): Flexible checks for parent-child rules.
"""

import logging
from pathlib import Path

import yaml
from anytree import Node, PreOrderIter

from .grammar import validate_leaf_consistency

__all__ = [
    "validate_ghosts",
    "validate_structure",
    "validate_tree",
    "validate_lexicon",
    "validate_metasyntax",
]

logger = logging.getLogger(__name__)

# --- CONSTANTS ---
GHOST_MARKER = "👻"


def load_validation_rules() -> dict:
    """
    Loads validation rules from the YAML specification.
    Returns a dictionary mapping tags to their rule definitions.
    """
    rules_map = {}
    try:
        # Path relative to this file: assets/rules/hybrid_rules.yaml
        rule_path = Path(__file__).parent / "assets" / "rules" / "hybrid_rules.yaml"
        if not rule_path.exists():
            logger.warning("Validation rules not found at %s", rule_path)
            return {}

        with open(rule_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for rule in data.get("rules", []):
            tag = rule.get("tag")
            if not tag:
                continue

            # Flatten allowed children
            children = rule.get("hijos_permitidos", {})
            allowed = set(
                children.get("obligatorios", []) + children.get("opcionales", [])
            )
            prohibited = set(rule.get("prohibiciones", []))

            rules_map[tag] = {
                "allowed": allowed,
                "prohibited": prohibited,
                "id": rule.get("id"),
            }

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to load validation rules: %s", e)

    return rules_map


# Initialize rules on module load
METASYNTAX_RULES = load_validation_rules()


def validate_ghosts(root: Node) -> list[str]:
    """
    STRICT: Checks for temporary 'ghost' nodes.
    Presence of ghosts implies the tree is unfinished.
    """
    errors = []
    if not root:
        return errors

    for node in PreOrderIter(root):
        # Check Node Name (Label)
        if GHOST_MARKER in node.name:
            errors.append(f"Ghost Node detected at: {node.name}")

        # Check 'word' attribute if present (Leaf)
        if hasattr(node, "word") and node.word and GHOST_MARKER in node.word:
            errors.append(f"Ghost Word detected in node: {node.name}")

    return errors


def validate_structure(root: Node) -> dict[Node, str]:
    """
    FLEXIBLE: Checks parent-child relationships against standard rules.
    Returns a dictionary mapping nodes to warning messages.
    """
    warnings = {}
    if not root:
        return warnings

    for node in PreOrderIter(root):
        if node.is_leaf:
            continue

        parent_label = node.name
        # Handle functional tags (e.g., "sn.suj" -> check rules for "sn")
        base_label = (
            parent_label.split(".")[0]
            if "." in parent_label and parent_label not in METASYNTAX_RULES
            else parent_label
        )

        if base_label in METASYNTAX_RULES:
            rule_def = METASYNTAX_RULES[base_label]
            allowed = rule_def["allowed"]
            prohibited = rule_def["prohibited"]

            for child in node.children:
                if child.is_leaf:
                    continue  # Skip text leaves

                child_label = child.name
                child_base = child_label.split(".")[0]

                # 1. Check Prohibitions (Explicitly Forbidden)
                if child_label in prohibited or child_base in prohibited:
                    warnings[child] = (
                        f"Prohibited Structure: '{parent_label}' cannot contain '{child_label}' "
                        f"(Rule: {rule_def['id']})"
                    )
                    continue

                # Permissive check: exact match OR base match
                if child_label not in allowed and child_base not in allowed:
                    warnings[child] = (
                        f"Unusual Structure: '{parent_label}' contains '{child_label}'"
                    )

    return warnings


# --- PUBLIC API EXPORTS ---
validate_lexicon = validate_leaf_consistency
validate_metasyntax = validate_structure


def validate_tree(root: Node) -> dict[Node, str]:
    """
    Comprehensive validation wrapper.
    Currently delegates to validate_metasyntax (structural rules).
    """
    return validate_structure(root)
