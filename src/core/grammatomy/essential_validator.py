from typing import Dict, List, Set, Tuple, Union

# ==========================================
# 1. Mapeo de Normalización (Identity for AnCora Native)
# ==========================================
# Mapeamos a las etiquetas nativas de AnCora que usa el modelo Stanza (ES).
GRUP_NOM = "grup.nom"
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
# Paradigmáticas (Set): {A, B} -> Requiere A O B.
# Sintagmáticas (Tuple): (A, B) -> Requiere A Y B en orden.
# Define qué es OBLIGATORIO para que un nodo sea válido.
# Usamos terminología AnCora.
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
# Definen qué hijos son legítimos dentro de un grupo.
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
    Validador de Estructura Esencial (AnCora Native).
    Valida árboles usando el estándar nativo de AnCora (sn, grup.nom, sentence).
    """

    def __init__(self):
        # La matriz se pre-calcula al iniciar para eficiencia.
        # Estructura: Dict[nodo, List[Niveles]]
        # Niveles es una lista de diccionarios: {Regla: [NodosFaltantes]}
        self.validation_matrix: Dict[str, List[Dict[Union[str, Tuple[str, ...]], List[str]]]] = {}
        self._build_matrix(max_depth=3)

    def _build_matrix(self, max_depth: int):
        """
        Construye la matriz de validación expandiendo recursivamente las reglas base.
        Genera las combinaciones válidas para niveles inferiores (aplanados).
        """
        for node_type, rules in BASE_RULES.items():
            self.validation_matrix[node_type] = self._build_levels_for_node(rules, max_depth)

    def _build_levels_for_node(
        self, rules: Set[Union[str, Tuple[str, ...]]], max_depth: int
    ) -> List[Dict[Union[str, Tuple[str, ...]], List[str]]]:
        levels = []

        # Nivel 0: Reglas directas (Estructura Canónica)
        # Inicialmente no falta nada (lista vacía)
        levels.append(self._extract_canonical_rules(rules))

        # Niveles 1..N: Expansión (Estructuras Aplanadas)
        for _ in range(max_depth):
            next_level = self._expand_level(levels[-1])
            if not next_level:
                break
            levels.append(next_level)

        return levels

    def _extract_canonical_rules(
        self, rules: Set[Union[str, Tuple[str, ...]]]
    ) -> Dict[Union[str, Tuple[str, ...]], List[str]]:
        current_level = {}
        for rule in rules:
            if isinstance(rule, (str, tuple)):
                current_level[rule] = []
        return current_level

    def _expand_level(
        self, prev_level: Dict[Union[str, Tuple[str, ...]], List[str]]
    ) -> Dict[Union[str, Tuple[str, ...]], List[str]]:
        next_level = {}
        for criteria, missing in prev_level.items():
            if isinstance(criteria, str):
                self._expand_paradigmatic(criteria, missing, next_level)
            elif isinstance(criteria, tuple):
                # Expansión Sintagmática: Expandimos los elementos de la secuencia.
                # Ej: (s, sn) -> (s, grup.nom) -> (s, n)
                self._expand_sequence(criteria, missing, next_level)
        return next_level

    def _expand_paradigmatic(self, criteria: str, current_missing: List[str], target_dict: Dict):
        # Expansión Paradigmática: Si el hijo requiere estructura, traemos sus opciones.
        # Ej: sn -> grup.nom -> {n, p...}
        if criteria in BASE_RULES:
            for sub_rule in BASE_RULES[criteria]:
                # Al expandir 'criteria', este nodo pasa a estar "perdido/implicito"
                new_missing = current_missing + [criteria]
                target_dict[sub_rule] = new_missing

    def _expand_sequence(
        self,
        sequence: Tuple[str, ...],
        current_missing: List[str],
        target_dict: Dict,
    ):
        """
        Expande una secuencia sintagmática sustituyendo no-terminales por sus reglas.
        Genera nuevas tuplas válidas para el siguiente nivel de aplanamiento.
        """
        # Convertimos a lista para mutar
        seq_list = list(sequence)
        expanded = False

        for i, item in enumerate(seq_list):
            if item in BASE_RULES:
                # Encontramos un nodo expandible (ej. 'sn' dentro de 'sp')
                sub_rules = BASE_RULES[item]
                for sub in sub_rules:
                    new_seq = seq_list.copy()
                    if isinstance(sub, str):
                        new_seq[i] = sub
                    elif isinstance(sub, tuple):
                        # Reemplazo de secuencia: (a, B, c) con B->(x,y) se vuelve (a, x, y, c)
                        new_seq[i : i + 1] = sub

                    # Al expandir 'item', este nodo pasa a estar "perdido/implicito"
                    new_missing = current_missing + [item]
                    target_dict[tuple(new_seq)] = new_missing
                expanded = True

        if not expanded:
            # Si no hay nada que expandir, es una secuencia terminal
            pass

    def validate_node(self, node_type: str, children_tags: List[str]) -> Tuple[bool, List[str]]:
        """
        Valida normalizando todo a Hybrid Syntax.
        """
        # 1. Normalización (AnCora/UD -> Hybrid)
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
        Verifica si 'sequence' aparece dentro de 'main_list' manteniendo el orden relativo.
        Ej: (prep, n) es subsecuencia de [prep, det, n, adj] -> True
        """
        it = iter(main_list)
        return all(any(c == item for c in it) for item in sequence)


# Ejemplo de uso (Simulación)
if __name__ == "__main__":
    validator = EssentialStructureValidator()

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
