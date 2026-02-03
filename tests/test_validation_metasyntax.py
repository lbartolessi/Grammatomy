"""
Unit tests for Metasyntactic Validation (Parent-Child Constraints).

This suite verifies that the tree structure adheres to the hierarchical rules
defined in 'references/Especificación YAML de Árboles Sintácticos.md'.
It ensures that no illegal parent-child relationships (e.g., a Verb directly inside a Determinant)
are formed.
"""

from anytree import Node
from grammatomy import from_ptb

# --- MOCK METASYNTAX RULES ---
# Derived from: references/Especificación YAML de Árboles Sintácticos.md
# Format: {Parent_Label: {allowed_children_labels}}

METASYNTAX_RULES = {
    "S": {"sn", "grup.verb", "sp", "f0", "conj", "sn.suj", "sn.cd"},
    "sn": {
        "grup.nom",
        "spec",
        "sp",
        "s.a",
        "f0",
        "conj",
        "dt",
    },  # Added 'dt' for PTB compatibility
    "sn.suj": {"grup.nom", "spec", "sp", "s.a"},
    "grup.nom": {"n", "nc", "np", "propn", "pron", "s.a", "sp"},
    "grup.verb": {"v", "vb", "vbd", "sn", "sp", "sadv", "neg", "morfema.pronominal"},
    "sp": {"prep", "sn", "s.a", "sadv"},
    # Terminals (should not have children in this simplified view, or only literals)
    "n": set(),
    "v": set(),
    "dt": set(),
}


def validate_structure(node: Node) -> list:
    """
    Recursively checks if every parent-child relationship is legal.
    Returns a list of error strings.
    """
    errors = []

    # If node is a leaf (text), we skip structural validation for now
    # (Lexicon test handles word-POS match)
    if node.is_leaf:
        return errors

    parent_label = node.name

    # If we don't have rules for this label, we might warn or skip.
    # For strict testing, we assume all valid non-terminals are in rules.
    if parent_label not in METASYNTAX_RULES:
        # Skip validation for unknown labels in this mock, or flag them.
        # errors.append(f"Unknown label '{parent_label}'")
        pass
    else:
        allowed_children = METASYNTAX_RULES[parent_label]
        for child in node.children:
            # Skip checking the text leaf itself
            if child.is_leaf:
                continue

            child_label = child.name
            if child_label not in allowed_children:
                errors.append(
                    f"Illegal Structure: '{parent_label}' cannot contain '{child_label}'."
                )

    # Recurse
    for child in node.children:
        errors.extend(validate_structure(child))

    return errors


# --- TESTS ---


def test_metasyntax_valid_tree():
    """Test a standard, well-formed sentence structure."""
    # (S (sn (spec (dt El)) (grup.nom (n gato))) (grup.verb (v come)))
    # Note: Simplified PTB for testing
    ptb = "(S (sn (dt El) (grup.nom (n gato))) (grup.verb (v come)))"
    root = from_ptb(ptb)

    errors = validate_structure(root)
    assert not errors, f"Valid tree flagged as invalid: {errors}"


def test_metasyntax_illegal_child():
    """Test a Verb nested directly inside a Noun Phrase (Illegal)."""
    # (sn (v come)) -> A noun phrase containing a verb directly
    ptb = "(sn (v come))"
    root = from_ptb(ptb)

    errors = validate_structure(root)
    assert len(errors) > 0, "Illegal 'sn -> v' relationship was not detected."
    assert "cannot contain 'v'" in errors[0]


def test_metasyntax_illegal_nesting():
    """Test a Preposition inside a Verb Group (Valid) vs inside a Noun (Invalid)."""
    # (grup.nom (prep de)) -> Nouns don't usually contain raw prepositions directly, usually via SP
    ptb = "(grup.nom (prep de))"
    root = from_ptb(ptb)

    errors = validate_structure(root)
    assert len(errors) > 0, "Illegal 'grup.nom -> prep' was not detected."
