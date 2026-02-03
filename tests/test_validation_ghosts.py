"""
Unit tests for Ghost Node Detection.

This suite verifies the safety mechanism described in 'references/Rigor_Linguistico.md' (Section 4).
Ghost Nodes (marked with '👻') are temporary placeholders inserted during manual editing.
The system must detect them and BLOCK export or final validation until resolved.
"""

import pytest
from anytree import Node, PreOrderIter

from grammatomy import from_ptb

# --- CONSTANTS ---
# The marker used by the UI to indicate an undefined node/word.
GHOST_MARKER = "👻"


def validate_no_ghosts(root: Node) -> list:
    """
    Traverses the tree to ensure no Ghost Nodes exist.
    Returns a list of error messages if ghosts are found.

    This function simulates the 'Export Guard' logic:
    If this returns errors, the 'Export' button in the UI should be disabled.
    """
    errors = []
    for node in PreOrderIter(root):
        # Check Node Name (Label/POS/Word)
        if GHOST_MARKER in node.name:
            errors.append(f"Ghost Node detected at: {node}")

        # Check custom attributes if they exist (e.g. 'word' or 'pos' in some parsers)
        # Note: LispParser might put the word in the name or an attribute depending on depth.
        if hasattr(node, "word") and node.word and GHOST_MARKER in node.word:
            errors.append(f"Ghost Word detected in node: {node}")

    return errors


# --- TESTS ---


def test_clean_tree_no_ghosts():
    """Verify that a normal, finished tree passes the ghost check."""
    # (S (sn (spec El) (grup.nom (n gato))) (grup.verb (v come)))
    ptb = "(S (sn (spec El) (grup.nom (n gato))) (grup.verb (v come)))"
    root = from_ptb(ptb)

    errors = validate_no_ghosts(root)
    assert not errors, f"Clean tree flagged as having ghosts: {errors}"


def test_ghost_in_pos_label():
    """Verify detection of a Ghost placeholder in a POS tag."""
    # Scenario: User created a new group but hasn't selected the category yet.
    # Structure: (S (sn (👻 gato)))
    ptb = f"(S (sn ({GHOST_MARKER} gato)))"
    root = from_ptb(ptb)

    errors = validate_no_ghosts(root)
    assert len(errors) > 0, "Ghost in POS label was not detected."
    assert "Ghost Node detected" in errors[0]


def test_ghost_in_word_leaf():
    """Verify detection of a Ghost placeholder in a terminal word."""
    # Scenario: User created a structure but hasn't typed the word.
    # Structure: (S (sn (n 👻)))
    ptb = f"(S (sn (n {GHOST_MARKER})))"
    root = from_ptb(ptb)

    errors = validate_no_ghosts(root)
    assert len(errors) > 0, "Ghost in leaf word was not detected."


def test_ghost_in_intermediate_group():
    """Verify detection of a Ghost placeholder in a phrasal node."""
    # Scenario: User is building a complex tree top-down.
    # Structure: (S (👻 (n gato))) -> Undefined phrase type
    ptb = f"(S ({GHOST_MARKER} (n gato)))"
    root = from_ptb(ptb)

    errors = validate_no_ghosts(root)
    assert len(errors) > 0, "Ghost in phrasal node was not detected."
