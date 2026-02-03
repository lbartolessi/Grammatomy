"""
Validation Module for Grammatomy.

Implements the core validation logic for the syntax tree:
1. Safety (Ghost Nodes): Strict checks for incomplete editing.
2. Structural Integrity (Metasyntax): Flexible checks for parent-child rules.
"""

from anytree import Node, PreOrderIter

# --- CONSTANTS ---
GHOST_MARKER = "👻"

# Simplified Metasyntax Rules (Hybrid AnCora/PTB)
# Used for warnings, not blocking.
METASYNTAX_RULES = {
    "S": {  # Sentence / Oración
        # AnCora (Spanish)
        "sn",
        "grup.verb",
        "sp",
        "f0",
        "conj",
        "sn.suj",
        "sn.cd",
        "inc",
        "interjeccio",
        "neg",
        "morfema.pronominal",
        "infinitiu",
        "relatiu",
        "gerundi",
        "participio",
        "participi",  # Variant
        "morfema.verbal",
        "s.a",  # Adjectival predicate / attribute
        "sadv",  # Adverbial predicate / adjunct
        "S",
        # PTB (English)
        "NP",
        "VP",
        "ADVP",
        "PP",
        "SBAR",
        "PRN",
        # Universal / Punctuation
        "PUNCT",
        ".",
        ",",
        # Italian / Universal
        "INTJ",
        # Universal Dependencies Conjunctions
        "SCONJ",
        "CCONJ",
    },
    "sn": {  # Sintagma Nominal (AnCora)
        "grup.nom",
        "spec",
        "sp",
        "s.a",
        "f0",
        "conj",
        "dt",
        "sn",
        "prep",  # Locutions or flat structures
        "relatiu",  # Relative pronouns acting as head
        # English/Universal mix safety
        "NP",
        "NNS",
        "NN",
        "PROPN",
        "PRON",
        "DET",
        # Portuguese (CINTIL / X-Bar)
        "N'",
        "CCONJ",
        "VERB",
        "ADV",
        # Italian (VIT)
        "spd",
        "sa",
        "savv",
        "NOUN",
        "SCONJ",  # 'que' introducing relative clauses often tagged as SCONJ
        "PUNCT",
    },
    "grup.nom": {  # Grupo Nominal (AnCora)
        "n",
        "nc",
        "np",
        "propn",
        "pron",
        "s.a",
        "sp",
        "sn",
        "f0",
        "w",
        # Hybrid: Allow UD tags inside AnCora groups
        "NOUN",
        "relatiu",
        "S",  # Subordinate clauses acting as nouns (Recursion)
        "PROPN",
        "PRON",
        "grup.nom",
        "conj",
        "num",
        "NUM",
        "CCONJ",
        "SCONJ",
    },
    "grup.verb": {
        "v",
        "vb",
        "vbd",
        "sn",
        "sp",
        "sadv",
        "neg",
        "morfema.pronominal",
        "gerundio",
        "gerundi",  # Variant
        "participio",
        "infinitivo",
        "infinitiu",  # Variant
        "f0",
        # Hybrid: Allow UD tags
        "VERB",
        "AUX",
        "s.a",
    },
    "sp": {  # Sintagma Preposicional (AnCora)
        "prep",
        "sn",
        "s.a",
        "sadv",
        "sp",  # Recursion (e.g. "de entre")
        "conj",  # Coordination inside PP
        "S",
        # Hybrid: Allow UD tags
        "ADP",
        "ADV",
        # Portuguese (CINTIL)
        "P'",
        "PUNCT",
        "PP",
        # Italian (VIT) - Flat structure
        "DET",
        "NOUN",
    },
    # --- English / PTB Rules (Standard) ---
    "NP": {
        "DT",
        "NN",
        "NNS",
        "NNP",
        "NNPS",
        "JJ",
        "ADJP",
        "PP",
        "SBAR",
        "PRP",
        "NP",
        "CC",
        "CD",
        "RB",
        "PUNCT",
        ".",
        ",",
        # Portuguese / Universal Compatibility
        "DET",
        "NOUN",
        "PROPN",
        "PRON",
        "CCONJ",
        "VERB",
        "ADV",
        "N'",
        # Italian / Universal
        "ADJ",
        "NUM",
    },
    "VP": {
        "VB",
        "VBD",
        "VBG",
        "VBN",
        "VBP",
        "VBZ",
        "MD",
        "NP",
        "PP",
        "ADJP",
        "SBAR",
        "ADVP",
        "PRT",
        "VP",
        "CC",
        "PUNCT",
        ".",
        ",",
        # Portuguese / Universal Compatibility
        "V'",
        "VERB",
        "AUX",
        # Italian / Universal
        "ADJ",
    },
    "PP": {
        "IN",
        "TO",
        "NP",
        "S",
        "SBAR",
        # Portuguese / Universal Compatibility
        "ADP",
        "ADV",
        "PUNCT",
        "PP",
        "P'",
    },
    "ADVP": {"RB", "RBR", "RBS", "JJ", "PP", "NP"},
    "SBAR": {"IN", "DT", "S", "SQ", "SINV", "WHNP", "WHADVP"},
}


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
            allowed = METASYNTAX_RULES[base_label]
            for child in node.children:
                if child.is_leaf:
                    continue  # Skip text leaves

                child_label = child.name
                child_base = child_label.split(".")[0]

                # Permissive check: exact match OR base match
                if child_label not in allowed and child_base not in allowed:
                    # We flag it, but in the UI this should be a warning, not an error
                    warnings[child] = (
                        f"Unusual Structure: '{parent_label}' contains '{child_label}'"
                    )

    return warnings
