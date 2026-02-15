"""
Essential Structure Validator.

This module provides a lightweight, rule-based validator that operates on a
pre-compiled "validation matrix". It is designed to quickly check if a given
syntactic structure conforms to the essential requirements of a grammar,
including flattened or collapsed variations.

The core idea is to pre-expand grammar rules into multiple levels of abstraction,
allowing for O(1) lookups during validation.
"""

from typing import Dict, List, Set, Tuple, Union

# ==========================================
# 1. Mapeo de Normalización (Identity for AnCora Native)
# ==========================================
#: Maps various syntactic tags to the native AnCora tags used by the Stanza (ES) model.
GRUP_NOM = "grup.nom"  #: Constant for Nominal Group.
GRUP_VERB = "grup.verb"
GRUP_A = "grup.a"
GRUP_ADV = "grup.adv"
NORMALIZE_TO_HYBRID = {
    # Identity mappings for AnCora tags
    "sn": "sn",
    GRUP_NOM: GRUP_NOM,
    GRUP_VERB: GRUP_VERB,
    "sp": "sp",
    GRUP_A: GRUP_A,
    GRUP_ADV: GRUP_ADV,
    "spec": "spec",
    "sentence": "sentence",
    "S": "S",
    "ROOT": "ROOT",
    "relatiu": "relatiu",
    # Map PTB tags to AnCora (fallback)
    "NP": "sn",
    "VP": GRUP_VERB,
    "PP": "sp",
    "ADJP": GRUP_A,
    "ADVP": GRUP_ADV,
    # POS Tags (UD Uppercase) - Identity
    "NOUN": "NOUN",
    "PROPN": "PROPN",
    "VERB": "VERB",
    "AUX": "AUX",
    "ADJ": "ADJ",
    "ADV": "ADV",
    "ADP": "ADP",
    "DET": "DET",
    "PRON": "PRON",
    "NUM": "NUM",
    "PUNCT": "PUNCT",
    "SYM": "SYM",
    "CCONJ": "CCONJ",
    "SCONJ": "SCONJ",
    # Legacy lowercase POS (AnCora original) -> UD Uppercase
    "n": "NOUN",
    "v": "VERB",
    "a": "ADJ",
    "r": "ADV",
    "d": "DET",
    "p": "PRON",
    "s": "ADP",
    "c": "CCONJ",
    "z": "NUM",
    "w": "NOUN",
    "f": "PUNCT",
}

# ==========================================
# 2. Definición de Reglas Base (Esenciales)
# ==========================================
#: Defines the essential, mandatory content for a node to be considered valid.
#: - Paradigmatic (Set): `{A, B}` -> Requires A OR B.
#: - Syntagmatic (Tuple): `(A, B)` -> Requires A AND B in order.
#: We use AnCora terminology.
BASE_RULES = {
    "ROOT": {"sentence"},
    "sentence": {GRUP_VERB},
    "S": {GRUP_VERB},
    "sn": {GRUP_NOM},
    GRUP_NOM: {"NOUN", "PROPN", "PRON", "NUM", "SYM"},
    GRUP_VERB: {"VERB", "AUX"},
    GRUP_A: {"ADJ"},
    GRUP_ADV: {"ADV"},
    "spec": {"DET", "NUM", "ADV"},
    "relatiu": {"PRON", "DET", "ADV"},
    # Reglas Sintagmáticas
    "sp": {("ADP", "sn"), ("ADP", GRUP_NOM), ("ADP", "S")},
}

# ==========================================
# 3. Reglas Topológicas (Contención Permitida)
# ==========================================
#: Defines which children are legitimate within a group.
TOPOLOGY_RULES = {
    "ROOT": {"sentence", "sn", GRUP_VERB, "sp", "PUNCT"},
    "sentence": {
        GRUP_VERB,
        "sn",
        "sp",
        GRUP_ADV,
        GRUP_A,
        "S",
        "coord",
        "inc",
        "PUNCT",
        # Permisividad para reconstrucción (absorción de POS)
        "VERB",
        "AUX",
        "NOUN",
        "PROPN",
        "PRON",
        "DET",
        "ADJ",
        "ADV",
    },
    "S": {
        GRUP_VERB,
        "sn",
        "sp",
        GRUP_ADV,
        GRUP_A,
        "S",
        "relatiu",
        "conj",
        "PUNCT",
        "VERB",
        "AUX",
        "NOUN",
        "PROPN",
        "PRON",
        "DET",
        "ADJ",
        "ADV",
    },
    "sn": {
        "spec",
        GRUP_NOM,
        "coord",
        "PUNCT",
        # Permisividad: sn puede absorber componentes de grup.nom si está aplanado
        "NOUN",
        "PROPN",
        "PRON",
        "ADJ",
        "sp",
        "S",
    },
    GRUP_NOM: {
        "NOUN",
        "PROPN",
        "PRON",
        "NUM",
        "SYM",  # Núcleos
        GRUP_A,
        "sp",
        "S",
        "sn",
        GRUP_NOM,  # Complementos / Aposición
        "coord",
        "PUNCT",
        "DET",
        "ADJ",  # DET permitido si spec está colapsado
    },
    GRUP_VERB: {
        "VERB",
        "AUX",
        "morfema.pronominal",
        "neg",
        "ADV",
        "PUNCT",
        GRUP_VERB,  # Recursividad para perífrasis
    },
    "sp": {
        "ADP",
        "sn",
        GRUP_NOM,
        "S",
        GRUP_ADV,
        "PUNCT",
        # Permisividad para reconstrucción
        "DET",
        "NOUN",
        "PROPN",
        "PRON",
        "ADJ",
    },
    GRUP_A: {"ADJ", GRUP_ADV, "sp", "spec", "PUNCT"},
    GRUP_ADV: {"ADV", "sp", "spec", "PUNCT"},
    "spec": {"DET", "NUM", "ADV", "PUNCT"},
    "relatiu": {"PRON", "DET", "ADV", "PUNCT"},
}


class EssentialStructureValidator:
    """
    Validates tree structures using a pre-compiled matrix of essential rules.

    This validator is optimized for speed by pre-calculating all valid
    "flattened" versions of the base grammar rules up to a certain depth.
    This allows it to validate collapsed structures (e.g., `sn -> NOUN`
    instead of `sn -> grup.nom -> NOUN`) efficiently.

    Attributes:
        validation_matrix (Dict): A multi-level dictionary mapping a node type
            to its valid child configurations at different levels of flattening.
    """

    def __init__(self):
        """Initializes the validator and builds the validation matrix."""
        self.validation_matrix: Dict[str, List[Dict[Union[str, Tuple[str, ...]], List[str]]]] = {}
        self._build_matrix(max_depth=3)

    def _build_matrix(self, max_depth: int):
        """
        Builds the validation matrix by recursively expanding the base rules.

        Args:
            max_depth (int): The maximum depth of rule expansion. A higher
                number allows for validating more heavily flattened trees.
        """
        for node_type, rules in BASE_RULES.items():
            self.validation_matrix[node_type] = self._build_levels_for_node(rules, max_depth)

    def _build_levels_for_node(
        self, rules: Set[Union[str, Tuple[str, ...]]], max_depth: int
    ) -> List[Dict[Union[str, Tuple[str, ...]], List[str]]]:
        """
        Builds the validation levels for a single node type.

        Args:
            rules: The set of base rules (paradigmatic or syntagmatic).
            max_depth: The maximum expansion depth.

        Returns:
            A list of dictionaries, where each dictionary represents a level
            of flattening.
        """
        levels = []

        # Level 0: Direct rules (Canonical Structure)
        levels.append(self._extract_canonical_rules(rules))

        # Levels 1..N: Expansion (Flattened Structures)
        for _ in range(max_depth):
            next_level = self._expand_level(levels[-1])
            if not next_level:
                break
            levels.append(next_level)

        return levels

    def _extract_canonical_rules(
        self, rules: Set[Union[str, Tuple[str, ...]]]
    ) -> Dict[Union[str, Tuple[str, ...]], List[str]]:
        """
        Creates the first level (L0) of the matrix from the base rules.

        At this level, no nodes are considered "missing" yet, so the value
        for each rule is an empty list.

        Returns:
            A dictionary representing the canonical rules.
        """
        current_level = {}
        for rule in rules:
            if isinstance(rule, (str, tuple)):
                current_level[rule] = []
        return current_level

    def _expand_level(
        self, prev_level: Dict[Union[str, Tuple[str, ...]], List[str]]
    ) -> Dict[Union[str, Tuple[str, ...]], List[str]]:
        """
        Creates the next level of the matrix by expanding the previous one.

        For each rule in the previous level, it substitutes non-terminal symbols
        with their own base rules, adding the substituted symbol to the "missing" list.

        Args:
            prev_level: The dictionary of rules from the previous level.

        Returns:
            A new dictionary representing the next level of flattening.
        """
        next_level = {}
        for criteria, missing in prev_level.items():
            if isinstance(criteria, str):
                self._expand_paradigmatic(criteria, missing, next_level)
            elif isinstance(criteria, tuple):
                self._expand_sequence(criteria, missing, next_level)
        return next_level

    def _expand_paradigmatic(self, criteria: str, current_missing: List[str], target_dict: Dict):
        """
        Expands a paradigmatic rule (a single string).
        Example: `sn` -> `grup.nom` -> `{n, p...}`

        Args:
            criteria: The non-terminal to expand (e.g., "grup.nom").
            current_missing: List of nodes already flattened to reach this point.
            target_dict: The dictionary for the next level to populate.
        """
        if criteria in BASE_RULES:
            for sub_rule in BASE_RULES[criteria]:
                # When expanding 'criteria', this node is now "missing/implicit"
                new_missing = current_missing + [criteria]
                target_dict[sub_rule] = new_missing

    def _expand_sequence(
        self,
        sequence: Tuple[str, ...],
        current_missing: List[str],
        target_dict: Dict,
    ):
        """
        Expands a syntagmatic rule (a tuple) by substituting non-terminals.
        Example: `(ADP, sn)` can be expanded to `(ADP, grup.nom)`.

        Args:
            sequence: The tuple of tags to expand.
            current_missing: List of nodes already flattened.
            target_dict: The dictionary for the next level to populate.
        """
        # Convert to list for mutation
        seq_list = list(sequence)
        expanded = False

        for i, item in enumerate(seq_list):
            if item in BASE_RULES:
                # Found an expandable node (e.g., 'sn' inside 'sp')
                sub_rules = BASE_RULES[item]
                for sub in sub_rules:
                    new_seq = seq_list.copy()
                    if isinstance(sub, str):
                        new_seq[i] = sub
                    elif isinstance(sub, tuple):
                        # Sequence replacement: (a, B, c) with B->(x,y) becomes (a, x, y, c)
                        new_seq[i : i + 1] = sub

                    # When expanding 'item', it becomes "missing/implicit"
                    new_missing = current_missing + [item]
                    target_dict[tuple(new_seq)] = new_missing
                expanded = True

        if not expanded:
            # If nothing was expanded, it's a terminal sequence.
            pass

    def validate_node(self, node_type: str, children_tags: List[str]) -> Tuple[bool, List[str]]:
        """
        Validates a node against the pre-built matrix.

        Args:
            node_type: The label of the node to validate.
            children_tags: A list of labels of its direct children.

        Returns:
            A tuple containing:
            - bool: True if the structure is valid, False otherwise.
            - List[str]: A list of implicitly "missing" nodes if valid, empty otherwise.
        """
        norm_node = NORMALIZE_TO_HYBRID.get(node_type, node_type)
        norm_children = [NORMALIZE_TO_HYBRID.get(t, t) for t in children_tags]

        if norm_node not in self.validation_matrix:
            return True, []

        levels = self.validation_matrix[norm_node]

        for level_dict in levels:
            match, missing = self._check_level_match(level_dict, norm_children)
            if match:
                return True, missing

        return False, []

    def _check_level_match(
        self, level_dict: Dict[Union[str, Tuple[str, ...]], List[str]], norm_children: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Checks if the children match any rule at a specific validation level.

        Args:
            level_dict: The dictionary of rules for the current level.
            norm_children: The normalized list of child tags.

        Returns:
            A tuple (match_found, list_of_missing_nodes).
        """
        for criteria, missing_nodes in level_dict.items():
            if isinstance(criteria, str):
                if criteria in norm_children:
                    return True, missing_nodes
            elif isinstance(criteria, tuple):
                if self._is_subsequence(criteria, norm_children):
                    return True, missing_nodes
        return False, []

    def _is_subsequence(self, sequence: Tuple[str, ...], main_list: List[str]) -> bool:
        """
        Checks if 'sequence' appears within 'main_list' while maintaining relative order.
        Example: `(prep, n)` is a subsequence of `[prep, det, n, adj]` -> True
        """
        it = iter(main_list)
        return all(any(c == item for c in it) for item in sequence)


if __name__ == "__main__":
    # Example Usage (Simulation)

    # Caso 1: SN aplanado (sn -> n)
    # sn requiere grup.nom, grup.nom requiere n.
    # Matriz sn: L0={grup.nom}, L1={n, p...}
    print(f"SN con 'n': {validator.validate_node('sn', ['n'])}")  # True

    # Caso 2: SP aplanado (sp -> prep, n)
    # sp requiere (prep, sn). sn -> grup.nom -> n.
    # Matriz sp: L0={(prep, sn)}, L1={(prep, grup.nom)}, L2={(prep, n)}
    print(f"SP con 'prep', 'n': {validator.validate_node('sp', ['prep', 'n'])}")  # True

    # Caso 3: SP incompleto (solo prep)
    print(f"SP con 'prep': {validator.validate_node('sp', ['prep'])}")  # False

    validator = EssentialStructureValidator()
