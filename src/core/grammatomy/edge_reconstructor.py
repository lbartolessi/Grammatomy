"""
Módulo de Reconstrucción de Aristas (EdgeBasedReconstructor).

Este módulo implementa algoritmos de refinamiento de árboles sintácticos
basados en estrategias de "Hidratación Mínima". Su objetivo es reparar
estructuras planas o degeneradas infiriendo nodos intermedios a partir
de patrones gramaticales conocidos (definidos en las reglas YAML).
"""

import logging
from pathlib import Path
from typing import List, Optional, Set, Tuple

from anytree import Node, PostOrderIter

from .essential_validator import NORMALIZE_TO_HYBRID
from .validation_engine import RECONSTRUCTION_BLACKLIST, ValidationEngine

logger = logging.getLogger(__name__)


class EdgeBasedReconstructor:
    """
    Refinador de árboles basado en Hidratación Mínima.

    Implementa una estrategia de recorrido Bottom-Up (Post-Order) para detectar
    secuencias de hijos que coinciden con patrones de producción gramatical.
    Agrupa estos nodos (Chunking) preservando el orden lineal.

    Attributes:
        engine (ValidationEngine): Motor de validación para consultar reglas.
        all_patterns (List): Lista aplanada y ordenada de patrones de producción.
    """

    #: Jerarquía de Prioridad para la aplicación de reglas.
    #: Nivel más bajo = Mayor prioridad (se intenta formar antes).
    HIERARCHY_LEVELS = {
        # Level 1: Core Constituents & Functional Heads (Inner Layer)
        "spec": 1,
        "grup.nom": 1,
        "grup.verb": 1,
        "grup.a": 1,
        "grup.adv": 1,
        "relatiu": 1,
        "morfema.pronominal": 1,
        "neg": 1,
        "coord": 1,
        "inc": 1,
        # Level 2: Phrasal Categories (Outer Layer)
        "sn": 2,
        "sp": 2,
        "s.a": 2,
        "s.adv": 2,
        # Level 3: Clauses & Sentences (Top Layer)
        "S": 3,
        "sentence": 3,
        "ROOT": 4,
    }

    def __init__(self):
        """
        Inicializa el reconstructor cargando las reglas híbridas.
        """
        # Load patterns via ValidationEngine (Singleton)
        rules_path = Path(__file__).resolve().parent / "assets" / "rules" / "hybrid_rules.yaml"
        self.engine = ValidationEngine(str(rules_path), "es")
        logger.info("EdgeBasedReconstructor initialized. Rules loaded from: %s", rules_path)

        # Patrones excluidos para evitar recursión infinita o sobre-generación
        self.pattern_blacklist = RECONSTRUCTION_BLACKLIST

        # Construir índice global de patrones: List of (PatternTuple, LHS_Tag)
        self.all_patterns: List[Tuple[Tuple[str, ...], str]] = []
        for tag, patterns in self.engine.patterns.items():
            for pat in patterns:
                # Exclude directly recursive patterns (where LHS appears in RHS)
                if tag in pat:
                    continue

                # Exclude blacklisted patterns from reconstruction logic
                if (tag, tuple(pat)) in self.pattern_blacklist:
                    continue

                self.all_patterns.append((tuple(pat), tag))

        # Ordenar patrones por:
        # 1. Hierarchy Level (Ascending) -> Prioritize inner constituents (grup.nom before sn)
        # 2. Length (Descending) -> Greedy match within the same level
        self.all_patterns.sort(key=lambda x: (self.HIERARCHY_LEVELS.get(x[1], 99), -len(x[0])))
        logger.debug("Loaded %d patterns for reconstruction.", len(self.all_patterns))

    def refine(self, root: Node) -> Tuple[Node, Set[Node]]:
        """
        Aplica el algoritmo de Hidratación Mínima al árbol.

        Args:
            root: Nodo raíz del árbol a refinar.

        Returns:
            Tupla (Árbol refinado, Set de nodos creados).
        """
        created_nodes: Set[Node] = set()

        # Bottom-up traversal (Post-Order)
        for node in PostOrderIter(root):
            if not node.children:
                continue

            # 1. Check validity (Filter)
            children_tags = [str(c.name) for c in node.children]
            is_valid, _, _ = self.engine.validate_node(
                str(node.name), children_tags, strategy="strict"
            )

            if is_valid:
                continue

            # 2. Try to repair
            created_in_node = self._repair_node(node)
            created_nodes.update(created_in_node)

        return root, created_nodes

    def _repair_node(self, node: Node) -> Set[Node]:
        """
        Intenta agrupar los hijos de un nodo basándose en patrones conocidos.

        Args:
            node: El nodo cuyos hijos se evaluarán.

        Returns:
            Set de nodos nuevos creados durante la reparación.
        """
        all_created_in_loop: Set[Node] = set()
        has_changed = True
        while has_changed:
            has_changed = False
            children = node.children
            children_tags = [NORMALIZE_TO_HYBRID.get(str(c.name), str(c.name)) for c in children]
            logger.debug("Repairing '%s'. Children: %s", node.name, children_tags)

            # Try patterns (longest first)
            for pattern, lhs in self.all_patterns:
                # Optimization: check if pattern is subsequence
                idx = self._find_subsequence(children_tags, pattern)

                if idx != -1:
                    logger.debug("Match found: %s -> %s at index %d", pattern, lhs, idx)
                    new_node = self._apply_pattern_match(node, lhs, idx, len(pattern))
                    if new_node:
                        all_created_in_loop.add(new_node)
                        has_changed = True
                        break  # Restart loop to handle new structure (e.g. ADP + sn -> sp)

        return all_created_in_loop

    def _apply_pattern_match(
        self, parent_node: Node, lhs: str, idx: int, pattern_len: int
    ) -> Optional[Node]:
        """
        Aplica una coincidencia de patrón: crea un nuevo nodo y mueve los hijos.

        Args:
            parent_node: Nodo padre actual.
            lhs: Etiqueta del nuevo nodo a crear (Left Hand Side de la regla).
            idx: Índice de inicio de la coincidencia en los hijos.
            pattern_len: Longitud del patrón coincidente.

        Returns:
            El nuevo nodo creado o None si las guardas lo impiden.
        """
        # 1. Recursion Guard: X -> X
        if lhs == str(parent_node.name):
            return None

        # 2. Topology Guard: ROOT is unique/top-level
        if lhs == "ROOT":
            return None

        # 3. Topology Guard: sentence is only allowed under ROOT
        if lhs == "sentence" and str(parent_node.name) != "ROOT":
            return None

        # Create new node
        new_node = Node(lhs)

        children = parent_node.children
        # Identify children to move
        sub_children = children[idx : idx + pattern_len]

        # Construct new children list for parent to preserve order
        mutable_children = list(children)
        pre = mutable_children[:idx]
        post = mutable_children[idx + pattern_len :]

        # Move sub children to new node
        for child in sub_children:
            child.parent = new_node

        # Attach new node to parent at correct position
        parent_node.children = pre + [new_node] + post

        return new_node

    def _find_subsequence(self, seq: List[str], subseq: Tuple[str, ...]) -> int:
        """
        Encuentra el índice de inicio de una subsecuencia dentro de una secuencia.

        Args:
            seq: La secuencia mayor (lista de etiquetas).
            subseq: La subsecuencia a buscar (patrón).

        Returns:
            Índice de inicio o -1 si no se encuentra.
        """
        n = len(subseq)
        if n == 0:
            return -1
        for i in range(len(seq) - n + 1):
            if tuple(seq[i : i + n]) == subseq:
                return i
        return -1
