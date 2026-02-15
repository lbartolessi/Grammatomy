"""
Motor de Validación Sintáctica (ValidationEngine).

Este módulo implementa el núcleo de validación para árboles sintácticos,
proporcionando mecanismos para verificar la consistencia estructural
basada en reglas gramaticales definibles (YAML). Actúa como oráculo
para determinar la legalidad de las operaciones en el árbol y soporta
estrategias de validación estricta y laxa.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from .grammar import PUNCTUATION_TAGS

#: Logger del módulo para trazas de validación y errores.
logger = logging.getLogger(__name__)

#: Patrones válidos gramaticalmente pero excluidos de la reconstrucción automática
#: para evitar recursividad infinita o sobre-generación.
#: Formato: {(Padre, (Hijo1, Hijo2, ...))}
RECONSTRUCTION_BLACKLIST = {
    ("grup.a", ("sn",)),
    ("grup.adv", ("sn",)),
    ("S", ("sn",)),
    ("sentence", ("sn",)),  # Fix: Permitir sn en sentence para validación
    # Prevent infinite recursion with 'inc' (inciso) wrapper cycles
    ("sentence", ("inc",)),
    ("S", ("inc",)),
    ("sn", ("inc",)),
    ("sp", ("inc",)),
    ("grup.nom", ("inc",)),
    ("grup.verb", ("inc",)),
    ("grup.a", ("inc",)),
    ("s.a", ("inc",)),
    ("grup.adv", ("inc",)),
    ("sadv", ("inc",)),
    ("spec", ("inc",)),
}

#: Etiquetas legacy de AnCora que no deberían aparecer en reglas compiladas
LEGACY_TAGS = {"n", "v", "a", "d", "r", "p", "c", "s", "f", "z", "w", "i"}


class ValidationEngine:
    """
    Motor de validación metasintáctica.

    Implementa el patrón Multiton para mantener una única instancia por
    combinación de archivo de reglas e idioma, optimizando la carga de
    configuraciones.

    Attributes:
        rules_path (Path): Ruta al archivo YAML de reglas.
        lang (str): Código de idioma (ej. 'es').
        rules (Dict): Diccionario maestro de reglas cargadas.
    """

    #: Cache de instancias para el patrón Multiton (path::lang -> instancia).
    _instances: Dict[str, "ValidationEngine"] = {}

    def __new__(cls, rules_path: str, lang: str):
        """Implementación del patrón Multiton."""
        key = f"{rules_path}::{lang}"
        if key not in cls._instances:
            instance = super(ValidationEngine, cls).__new__(cls)
            cls._instances[key] = instance
            instance._initialized = False
        return cls._instances[key]

    def __init__(self, rules_path: str, lang: str):
        """
        Inicializa el motor de validación.

        Args:
            rules_path: Ruta al archivo de reglas .yaml.
            lang: Idioma objetivo (ej. 'es').
        """
        if getattr(self, "_initialized", False):
            return

        self.rules_path = Path(rules_path)
        self.lang = lang.lower()

        # Estructuras optimizadas para O(1)
        self.rules: Dict[str, Any] = {}
        self.allowed_children: Dict[str, Set[str]] = {}
        self.allowed_parents: Dict[str, Set[str]] = {}
        self.mandatory_children: Dict[str, Set[str]] = {}
        self.patterns: Dict[str, List[List[str]]] = {}
        self._reverse_index: Dict[str, Set[str]] = {}
        self._variant_map: Dict[str, str] = {}
        self.terminal_parents: Set[str] = set()
        self.root_allowed_tags: Set[str] = set()

        self._load_rules()
        self._validate_consistency()
        self._derive_constraints_from_patterns()
        self._synchronize_parent_child_constraints()
        self._apply_structural_patches()
        self._initialized = True

    # --- Métodos Públicos (API) ---

    def get_valid_substitutions(self, parent: Optional[str], children: List[str]) -> List[str]:
        """
        Retorna una lista de etiquetas candidatas que son simultáneamente compatibles
        con el padre dado y los hijos existentes.

        Args:
            parent: Etiqueta del nodo padre (o None si es raíz).
            children: Lista de etiquetas de los hijos actuales.

        Returns:
            Lista ordenada de etiquetas válidas para sustitución.
        """
        candidates = self.rules.keys()
        valid_options = [
            tag for tag in candidates if self._is_substitution_candidate(tag, parent, children)
        ]
        return sorted(valid_options)

    def get_definition(self, tag: str) -> Dict[str, Any]:
        """
        Retorna la definición cruda de una etiqueta para mostrar en el Inspector.

        Args:
            tag: La etiqueta a consultar.

        Returns:
            Diccionario con la configuración del nodo o vacío si no existe.
        """
        if not self.rules:
            logger.warning("Rules registry is empty. Attempting lazy reload...")
            self._load_rules()

        val = self.rules.get(tag, {})
        if not val:
            logger.warning(
                "⚠️ MISSING DEFINITION: Requested tag='%s' (len=%d). Available keys sample: %s",
                tag,
                len(tag),
                list(self.rules.keys())[:5],
            )
        return val

    def get_all_tags(self) -> List[str]:
        """
        Retorna lista ordenada de todas las etiquetas conocidas en las reglas.
        """
        return sorted(self.rules.keys())

    def can_add_child(
        self, parent_tag: str, child_tag: str, strategy: str = "strict"
    ) -> Tuple[bool, str]:
        """
        Verifica si un nodo padre puede contener a un hijo específico.

        Args:
            parent_tag: Etiqueta del padre.
            child_tag: Etiqueta del hijo propuesto.
            strategy: 'strict' (reglas explícitas) o 'lax' (permisivo).

        Returns:
            Tupla (Es válido, Mensaje de razón).
        """
        if strategy == "lax":
            return True, "Lax Mode: Context check bypassed."

        # Fix: Allow punctuation universally in context checks to avoid false positives
        if child_tag in PUNCTUATION_TAGS:
            return True, "OK"

        if parent_tag not in self.allowed_children:
            if not self.rules:
                return True, "Permissive Mode (No rules)"
            return False, f"Node '{parent_tag}' is a terminal or has no rules defined."

        if child_tag not in self.allowed_children[parent_tag]:
            if not self.allowed_children[parent_tag] and child_tag not in self.rules:
                return True, "OK"

            return (
                False,
                f"'{parent_tag}' does not allow '{child_tag}'. "
                f"Allowed: {sorted(self.allowed_children[parent_tag])}",
            )

        return True, "OK"

    def can_convert_node(
        self,
        ancestor_tags: List[str],
        current_children_tags: List[str],
    ) -> List[str]:
        """
        Determina si un nodo puede cambiar su etiqueta (ej. de NP a VP)
        manteniendo la coherencia con sus ancestros e hijos.

        Args:
            ancestor_tags: Lista de etiquetas de los ancestros.
            current_children_tags: Lista de etiquetas de los hijos actuales.

        Returns:
            Lista de etiquetas válidas para esa posición.
        """
        candidates = set(self.rules.keys())
        ancestors_set = set(ancestor_tags)

        if ancestors_set:
            candidates = {
                tag
                for tag in candidates
                if not self.allowed_parents.get(tag, set()).isdisjoint(ancestors_set)
            }
        else:
            candidates = set(self.rules.keys())

        for child in current_children_tags:
            if child in self.rules:
                valid_parents_for_child = self._reverse_index.get(child, set())
            else:
                valid_parents_for_child = self.terminal_parents
            candidates &= valid_parents_for_child

        return sorted(candidates)

    def get_valid_parents(self, child_tag: str) -> List[str]:
        """
        Retorna una lista de etiquetas padre que permiten al hijo dado.
        Utiliza el índice inverso para búsquedas O(1).

        Args:
            child_tag: Etiqueta del nodo hijo.
        """
        parents = self._reverse_index.get(child_tag, set())
        if not parents and child_tag in self._variant_map:
            canonical = self._variant_map[child_tag]
            parents = self._reverse_index.get(canonical, set())
        return sorted(parents)

    def validate_node(
        self,
        node_label: str,
        children_labels: List[str],
        descendants_labels: Optional[List[str]] = None,
        strategy: str = "lax",
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Valida la estructura interna de un nodo.

        Args:
            node_label: Etiqueta del nodo a validar.
            children_labels: Etiquetas de los hijos directos.
            descendants_labels: Etiquetas de todos los descendientes (para modo laxo).
            strategy: Estrategia de validación ('strict' o 'lax').

        Returns:
            Tupla (Es válido, Lista de errores, Traza de depuración).
        """
        errors = []
        trace = []

        if node_label not in self.rules:
            return True, [], []

        node_config = self.rules.get(node_label, {})
        node_type = node_config.get("type", "group")

        if node_type == "leaf":
            return True, [], []

        if strategy == "strict":
            self._validate_strict(node_label, children_labels, errors, trace)

        elif strategy == "lax":
            self._validate_lax(node_label, children_labels, descendants_labels, errors, trace)

        return len(errors) == 0, errors, trace

    def can_delete_child(
        self, parent_tag: str, child_tag: str, sibling_tags: List[str]
    ) -> Tuple[bool, str]:
        """
        Verifica si es legal borrar un hijo, respetando restricciones de obligatoriedad.

        Args:
            parent_tag: Etiqueta del padre.
            child_tag: Etiqueta del hijo a borrar.
            sibling_tags: Etiquetas de los hermanos (incluyendo el que se borra).

        Returns:
            Tupla (Es válido, Mensaje).
        """
        if not self.rules:
            return True, "Permissive Mode"

        mandatory_set = self.mandatory_children.get(parent_tag, set())

        if child_tag in mandatory_set:
            # Si es obligatorio, verificamos si queda otro igual en los hermanos
            # (excluyendo una instancia del que se va a borrar)
            remaining_siblings = list(sibling_tags)
            if child_tag in remaining_siblings:
                remaining_siblings.remove(child_tag)

            if child_tag not in remaining_siblings:
                return (
                    False,
                    f"Cannot delete '{child_tag}': Node '{parent_tag}' "
                    f"requires '{child_tag}' (Mandatory).",
                )

        return True, "OK"

    # --- Métodos Privados (Carga y Lógica Interna) ---

    def _load_rules(self):
        """Carga y procesa el archivo de reglas YAML."""
        if not self.rules_path.exists():
            logger.error("Rules file not found: %s", self.rules_path)
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.error("Rules file is empty or invalid YAML: %s", self.rules_path)
                return

            if not self._check_language_compatibility(data):
                return

            self._parse_nodes(data.get("nodes", []))
            self._build_reverse_index()

            logger.info(
                "ValidationEngine loaded %d rules from %s", len(self.rules), self.rules_path
            )

        except Exception as e:
            logger.error("Error loading rules: %s", e)
            raise

    def _check_language_compatibility(self, data: Dict[str, Any]) -> bool:
        config = data.get("tree_config", {})
        rule_lang = config.get("language")

        if rule_lang and rule_lang.lower() != self.lang:
            logger.warning(
                "Rules language '%s' does not match requested '%s'. Enabling Permissive Mode.",
                rule_lang,
                self.lang,
            )
            return False
        return True

    def _parse_nodes(self, raw_nodes: Any):
        self.rules = {}
        if isinstance(raw_nodes, dict):
            self._parse_nodes_dict(raw_nodes)
        elif isinstance(raw_nodes, list):
            self._parse_nodes_list(raw_nodes)
        else:
            logger.error("Invalid 'nodes' section in rules file. Expected list or dict.")

    def _parse_nodes_dict(self, raw_nodes: Dict[str, Any]):
        for tag, node_data in raw_nodes.items():
            if isinstance(node_data, dict):
                if "id" not in node_data:
                    node_data["id"] = tag
                self._process_single_node(node_data, tag)

    def _parse_nodes_list(self, raw_nodes: List[Any]):
        for node in raw_nodes:
            if isinstance(node, dict):
                self._process_single_node(node, node.get("id"))

    def _process_single_node(self, node: Dict[str, Any], tag: Optional[str]):
        if not tag:
            return
        self.rules[tag] = node

        # Normalización para formato legacy
        if "allowed_children" not in node and "rules" in node:
            rules = node["rules"]
            strict_rules = rules.get("strict", {})
            all_rules = rules.get("all", {})
            mandatory_complex = strict_rules.get("mandatory_children", [])
            allowed_legacy = all_rules.get("allowed_children", [])
            node["allowed_children"] = {
                "mandatory": mandatory_complex,
                "optional": allowed_legacy,
            }

        children_config = node.get("allowed_children", {})
        if children_config:
            if isinstance(children_config, list):
                # Handle simplified list format (treat as allowed/optional)
                self.allowed_children[tag] = set(children_config)
                self.mandatory_children[tag] = set()
            else:
                optional = children_config.get("optional", []) or []
                mandatory = children_config.get("mandatory", []) or []

                # Fix: Asegurar que los hijos obligatorios (si son strings) también sean permitidos
                mandatory_strings = {m for m in mandatory if isinstance(m, str)}

                # Fix: Aplanar estructuras complejas en mandatory (listas de opciones) para allowed_children
                mandatory_complex = set()
                for m in mandatory:
                    if isinstance(m, list):
                        mandatory_complex.update(m)
                self.allowed_children[tag] = set(optional) | mandatory_strings | mandatory_complex

                self.mandatory_children[tag] = mandatory_strings

            # Sanity Check: Warn if legacy tags persist in compiled rules
            if not self.allowed_children[tag].isdisjoint(LEGACY_TAGS):
                legacy_found = self.allowed_children[tag].intersection(LEGACY_TAGS)
                logger.warning(
                    f"⚠️  Legacy tags found in '{tag}': {legacy_found}. Rules might need recompilation."
                )
        else:
            self.allowed_children[tag] = set()
            self.mandatory_children[tag] = set()

        self.patterns[tag] = node.get("patterns", [])
        self.allowed_parents[tag] = set(node.get("allowed_parents", []) or [])

        if not self.allowed_children[tag] and not self.patterns[tag]:
            self.terminal_parents.add(tag)

        if node.get("root_allowed", False):
            self.root_allowed_tags.add(tag)

        self._register_variants(node, tag)

    def _register_variants(self, node: Dict[str, Any], tag: str):
        for variant in node.get("functional_variants", []) or []:
            self._variant_map[variant] = tag
            self.rules[variant] = node
            self.allowed_children[variant] = self.allowed_children[tag]
            self.allowed_parents[variant] = self.allowed_parents[tag]
            self.mandatory_children[variant] = self.mandatory_children[tag]
            self.patterns[variant] = self.patterns[tag]
            if tag in self.root_allowed_tags:
                self.root_allowed_tags.add(variant)

    def _derive_constraints_from_patterns(self):
        """
        Deriva allowed_children y mandatory_children directamente de los patrones.
        """
        # 0. Inyectar patrones de la lista negra (Sincronización)
        # Esto asegura que los hijos sean válidos aunque el patrón esté prohibido para reconstruir.
        for tag, pattern_tuple in RECONSTRUCTION_BLACKLIST:
            if tag not in self.patterns:
                self.patterns[tag] = []
            pattern_list = list(pattern_tuple)
            if pattern_list not in self.patterns[tag]:
                self.patterns[tag].append(pattern_list)

        for tag, patterns in self.patterns.items():
            if not patterns:
                continue

            # 1. Derive Allowed Children
            derived_allowed = set()
            for pattern in patterns:
                derived_allowed.update(pattern)

            # Fix: Ensure tag exists in allowed_children before updating (Robustness for missing rules)
            if tag not in self.allowed_children:
                self.allowed_children[tag] = set()
            self.allowed_children[tag].update(derived_allowed)

            # 2. Derive Mandatory Children (Intersección)
            if patterns:
                intersection = set(patterns[0])
                for pattern in patterns[1:]:
                    intersection &= set(pattern)
                if tag not in self.mandatory_children:
                    self.mandatory_children[tag] = set()
                self.mandatory_children[tag].update(intersection)

            # 3. Update Reverse Index (Child -> Parents)
            for child in self.allowed_children[tag]:
                if child not in self._reverse_index:
                    self._reverse_index[child] = set()
                self._reverse_index[child].add(tag)

    def _synchronize_parent_child_constraints(self):
        """
        Sincroniza bidireccionalmente las restricciones:
        Si un hijo declara un padre permitido en 'allowed_parents',
        el padre debe actualizarse para permitir a ese hijo.
        """
        for child, parents in self.allowed_parents.items():
            for parent in parents:
                if parent in self.allowed_children:
                    self.allowed_children[parent].add(child)
                    # Mantener coherencia en el índice inverso
                    if child not in self._reverse_index:
                        self._reverse_index[child] = set()
                    self._reverse_index[child].add(parent)

    def _apply_structural_patches(self):
        """
        Aplica parches estructurales para relaciones conocidas que suelen faltar
        en las definiciones estrictas o importadas.
        """
        # Patch: 'spec' is a valid child of 'sn' (Determiner/Quantifier)
        if "sn" in self.allowed_children:
            self.allowed_children["sn"].add("spec")
            self._reverse_index.setdefault("spec", set()).add("sn")

    def _build_reverse_index(self):
        for tag, children in self.allowed_children.items():
            for child in children:
                if child not in self._reverse_index:
                    self._reverse_index[child] = set()
                self._reverse_index[child].add(tag)

    def _validate_consistency(self):
        """Verifica la coherencia bidireccional de las reglas al inicio."""

    def _is_substitution_candidate(
        self, tag: str, parent: Optional[str], children: List[str]
    ) -> bool:
        # Regla 1: Compatibilidad hacia arriba
        if parent:
            is_valid_child, _ = self.can_add_child(parent, tag)
            if not is_valid_child:
                return False
        elif tag not in self.root_allowed_tags:
            return False

        # Regla 2: Compatibilidad hacia abajo
        for child in children:
            if "👻" in child:
                continue
            is_valid_grandchild, _ = self.can_add_child(tag, child)
            if not is_valid_grandchild:
                return False

        return True

    def _validate_strict(
        self, node_label: str, children_labels: List[str], errors: List[str], trace: List[str]
    ):
        allowed = self.allowed_children.get(node_label, set())

        # 1. Illegal Children
        for child in children_labels:
            # Ignore punctuation and ghost nodes in strict check
            if child in PUNCTUATION_TAGS or child == "👻":
                continue

            if child not in allowed:
                msg = f"Strict: Node '{node_label}' cannot contain '{child}'."
                errors.append(msg)
                trace.append(
                    f"❌ Checked children of '{node_label}': Found illegal child '{child}'."
                )
                trace.append(f"   Allowed: {sorted(list(allowed))}")

        # 2. Mandatory Patterns (Contiguous Subsequence Check)
        node_patterns = self.patterns.get(node_label, [])
        if node_patterns:
            # Filter out punctuation and ghost nodes for pattern matching
            clean_children = [c for c in children_labels if c not in PUNCTUATION_TAGS and c != "👻"]

            has_match = False
            for pattern in node_patterns:
                if self._contains_contiguous_subsequence(clean_children, pattern):
                    has_match = True
                    break

            if not has_match:
                msg = f"Strict: Node '{node_label}' does not contain any valid production pattern."
                errors.append(msg)
                trace.append(
                    f"❌ Pattern Check for '{node_label}': Children {clean_children} (filtered) "
                    f"do not match any of {node_patterns}."
                )

    def _validate_lax(
        self,
        node_label: str,
        children_labels: List[str],
        descendants_labels: Optional[List[str]],
        errors: List[str],
        trace: List[str],
    ):
        scope_labels = descendants_labels if descendants_labels is not None else children_labels

        if children_labels:
            trace.append("ℹ️ Lax Mode: Skipping 'Allowed Children' check to accommodate flattening.")

        mandatory_set = self.mandatory_children.get(node_label, set())

        for req_child in mandatory_set:
            if not self._check_yield_presence(req_child, scope_labels):
                msg = f"Lax: Node '{node_label}' is missing essential content '{req_child}'."
                errors.append(msg)
                trace.append(f"❌ Recursive Yield Check for '{node_label}': Missing '{req_child}'.")

    def _contains_contiguous_subsequence(self, sequence: List[str], pattern: List[str]) -> bool:
        """Checks if 'pattern' exists as a contiguous subsequence within 'sequence'."""
        n = len(pattern)
        if n == 0:
            return True
        for i in range(len(sequence) - n + 1):  # pylint: disable=consider-using-enumerate
            if sequence[i : i + n] == pattern:
                return True
        return False

    def _check_yield_presence(self, target_type: str, context_labels: List[str]) -> bool:
        """
        Verifica recursivamente si 'target_type' o su contenido obligatorio está presente.
        """
        # 1. Direct Presence
        if target_type in context_labels:
            return True

        # 2. Recursive Yield Check
        # We use the derived mandatory children (intersection of patterns)
        target_mandatory = self.mandatory_children.get(target_type, set())

        # If no mandatory children, we can't enforce presence via recursion
        if not target_mandatory:
            is_leaf = self.rules.get(target_type, {}).get("type") == "leaf"
            return not is_leaf

        # Check if ALL mandatory children of the target are present in context
        for sub_req in target_mandatory:
            if not self._check_yield_presence(sub_req, context_labels):
                return False

        return True
