"""
Unit tests for the Lexicon Validation Hook mechanism.

This test suite mocks the external lexicon validation logic defined in
references/Rigor_Linguistico.md to ensure the system correctly identifies
lexical and POS mismatches.

STRICTNESS LEVEL: CLOSED WORLD
As per user specification, this test assumes a strict lexicon.
If a word is not in the lexicon, it is considered INVALID.
Tags must align with 'references/Especificación YAML de Árboles Sintácticos.md'.
"""

import pytest
from anytree import Node

from grammatomy import from_ptb

# --- MOCK INFRASTRUCTURE ---

# A tiny lexicon for testing purposes.
# Format: {word_lowercase: {valid_pos_tags}}
# Tags aligned with YAML Specification (AnCora/Hybrid):
# n: Nombre, v: Verbo, prep: Preposición, spec: Especificador (Determinante), f0: Puntuación
MOCK_LEXICON = {
    "el": {"spec", "dt"},  # 'spec' in AnCora, 'dt' often used in hybrid PTB
    "gato": {"n", "nc"},  # 'n' in YAML
    "come": {"v"},  # 'v' in YAML
    "pescado": {"n", "nc"},
    "de": {"prep"},  # 'prep' in YAML
    ".": {"f0", "fp", "."},  # 'f0' in YAML
}


def mock_lexicon_hook(word: str, pos: str) -> bool:
    """
    Simulates the LEXICON_HOOK described in architectural principles.
    Strict Mode: Returns True ONLY if word exists AND pos matches.
    """
    normalized = word.lower()
    if normalized not in MOCK_LEXICON:
        return False  # Unknown word -> Invalid

    valid_tags = MOCK_LEXICON[normalized]
    return pos in valid_tags


def validate_tree_lexicon(root: Node, hook_func) -> list:
    """
    Traverses the tree and validates leaves against the hook.
    Returns a list of tuples (word, pos, is_valid).
    """
    results = []
    for node in root.descendants:
        if node.is_leaf:
            # In PTB structure (POS (Word)), the leaf is the word, parent is POS.
            word = node.name
            pos_node = node.parent

            if pos_node:
                pos = pos_node.name
                is_valid = hook_func(word, pos)
                results.append((word, pos, is_valid))
    return results


# --- TESTS ---


def test_lexicon_all_valid():
    """
    Scenario A: Sentence contains ONLY lexicon words under correct categories.
    Result: All nodes must be valid.
    """
    # "El gato come pescado."
    # Structure follows YAML: sn -> spec/grup.nom -> n
    ptb = "(S (sn (spec El) (grup.nom (n gato))) (grup.verb (v come) (sn (grup.nom (n pescado)))) (f0 .))"
    root = from_ptb(ptb)

    validation_results = validate_tree_lexicon(root, mock_lexicon_hook)

    # Assert no errors found
    for word, pos, is_valid in validation_results:
        assert is_valid, f"Expected VALID: Word '{word}' under '{pos}'."


def test_lexicon_mixed_validity():
    """
    Scenario B: Sentence contains mixed known/unknown words.
    Result: Known words valid, unknown words invalid.
    """
    # "El perro come." -> 'perro' is unknown (invalid), 'El'/'come' are known (valid).
    ptb = "(S (sn (spec El) (grup.nom (n perro))) (grup.verb (v come)) (f0 .))"
    root = from_ptb(ptb)

    validation_results = validate_tree_lexicon(root, mock_lexicon_hook)

    # Convert to dict for easier checking
    res_dict = {word: valid for word, _, valid in validation_results}

    assert res_dict["El"] is True, "'El' should be valid."
    assert res_dict["come"] is True, "'come' should be valid."
    assert res_dict["perro"] is False, "'perro' should be INVALID (not in lexicon)."


def test_lexicon_all_invalid():
    """
    Scenario C: Sentence contains NO words from the lexicon.
    Result: All nodes must be marked as invalid.
    """
    # "Un perro ladra" -> None of these are in MOCK_LEXICON.
    ptb = "(S (sn (spec Un) (grup.nom (n perro))) (grup.verb (v ladra)))"
    root = from_ptb(ptb)

    validation_results = validate_tree_lexicon(root, mock_lexicon_hook)

    for word, pos, is_valid in validation_results:
        assert is_valid is False, f"Expected INVALID: Word '{word}' (not in lexicon)."


def test_lexicon_pos_mismatch_yaml():
    """
    Scenario D: Words exist but are under wrong YAML category.
    Result: Invalid.
    """
    # "gato" (n) tagged as 'v' (Verbo).
    ptb = "(S (grup.verb (v gato)))"
    root = from_ptb(ptb)

    validation_results = validate_tree_lexicon(root, mock_lexicon_hook)

    for word, pos, is_valid in validation_results:
        assert is_valid is False, f"Mismatch '{word}' as '{pos}' should be detected."
