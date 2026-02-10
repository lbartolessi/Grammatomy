import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Motor de validación metasintáctica.
    Actúa como oráculo para determinar la legalidad de las operaciones en el árbol.
    Implementa patrón Multiton (cache por path+lang) para eficiencia.
    """

    _instances: Dict[str, "ValidationEngine"] = {}

    def __new__(cls, rules_path: str, lang: str):
        key = f"{rules_path}::{lang}"
        if key not in cls._instances:
            instance = super(ValidationEngine, cls).__new__(cls)
            cls._instances[key] = instance
            instance._initialized = False
        return cls._instances[key]

    def __init__(self, rules_path: str, lang: str):
        if getattr(self, "_initialized", False):
            return

        self.rules_path = Path(rules_path)
        self.lang = lang.lower()

        # Estructuras optimizadas para O(1)
        self.rules: Dict[str, Any] = {}
        self.allowed_children: Dict[str, Set[str]] = {}
        self.allowed_parents: Dict[str, Set[str]] = {}
        self.mandatory_children: Dict[str, Set[str]] = {}
        self.patterns: Dict[str, List[List[str]]] = {}  # New: Production patterns
        self._reverse_index: Dict[str, Set[str]] = {}  # Derived index: Child -> Valid Parents
        self._variant_map: Dict[str, str] = {}  # Variant -> Canonical Tag
        self.terminal_parents: Set[str] = set()  # Tags that allow terminals (empty allowed list)
        self.root_allowed_tags: Set[str] = set()

        self._load_rules()
        self._validate_consistency()
        self._derive_constraints_from_patterns()
        self._initialized = True

    def _load_rules(self):
        if not self.rules_path.exists():
            logger.error("Rules file not found: %s", self.rules_path)
            print(f"[ERROR] Rules file not found: {self.rules_path}")
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.error("Rules file is empty or invalid YAML: %s", self.rules_path)
                print(f"[ERROR] Rules file is empty/invalid: {self.rules_path}")
                return

            if not self._check_language_compatibility(data):
                return

            self._parse_nodes(data.get("nodes", []))
            self._build_reverse_index()

            logger.info(
                "ValidationEngine loaded %d rules from %s", len(self.rules), self.rules_path
            )
            logger.debug("Sample keys: %s", list(self.rules.keys())[:5])
            print(f"[INFO] Loaded {len(self.rules)} rules from {self.rules_path}")

        except Exception as e:
            logger.error("Error loading rules: %s", e)
            print(f"[ERROR] Exception loading rules: {e}")
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

        # --- Normalization for Legacy Format (rules_es.yaml) ---
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
            # In new format, 'mandatory' is removed from YAML and derived from patterns.
            # We only load 'optional' here.
            optional = children_config.get("optional", []) or []
            mandatory = children_config.get("mandatory", []) or []
            self.allowed_children[tag] = set(optional)
            # Mandatory is seeded from YAML (for legacy/testing) and augmented by patterns
            # Filter out complex mandatory rules (lists) to avoid TypeError: unhashable type: 'list'
            self.mandatory_children[tag] = {m for m in mandatory if isinstance(m, str)}
            if mandatory and not self.mandatory_children[tag]:
                logger.warning(
                    "Tag '%s' has complex mandatory children %s which were filtered out.",
                    tag,
                    mandatory,
                )
        else:
            self.allowed_children[tag] = set()
            self.mandatory_children[tag] = set()

        # Load patterns
        self.patterns[tag] = node.get("patterns", [])
        if self.patterns[tag]:
            logger.debug("Loaded %d patterns for tag '%s'", len(self.patterns[tag]), tag)

        self.allowed_parents[tag] = set(node.get("allowed_parents", []) or [])

        if not self.allowed_children[tag] and not self.patterns[tag]:
            self.terminal_parents.add(tag)

        if node.get("root_allowed", False):
            self.root_allowed_tags.add(tag)

        self._register_variants(node, tag)

    def _register_variants(self, node: Dict[str, Any], tag: str):
        for variant in node.get("functional_variants", []) or []:
            logger.debug("Registering variant: '%s' -> '%s'", variant, tag)
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
        Derives allowed_children and mandatory_children directly from the loaded patterns.
        This ensures that any component used in a production rule is legally allowed.
        """
        for tag, patterns in self.patterns.items():
            if not patterns:
                continue

            # 1. Derive Allowed Children (Union of all symbols in patterns)
            derived_allowed = set()
            for pattern in patterns:
                derived_allowed.update(pattern)

            # Merge with existing allowed (preserves manually defined optional children)
            self.allowed_children[tag].update(derived_allowed)

            # 2. Derive Mandatory Children (Intersection of all patterns)
            # If a child appears in ALL patterns, it is mandatory.
            # Note: This is a heuristic. With shortcuts (e.g. sn -> NOUN), intersection might be empty.
            if patterns:
                intersection = set(patterns[0])
                for pattern in patterns[1:]:
                    intersection &= set(pattern)
                self.mandatory_children[tag].update(intersection)

            # 3. Derive Allowed Parents (Reverse Index)
            for child in derived_allowed:
                self._reverse_index.setdefault(child, set()).add(tag)

    def _build_reverse_index(self):
        for tag, children in self.allowed_children.items():
            for child in children:
                if child not in self._reverse_index:
                    self._reverse_index[child] = set()
                self._reverse_index[child].add(tag)

    def _validate_consistency(self):
        """Verifica la coherencia bidireccional de las reglas al inicio."""

    def get_valid_substitutions(self, parent: Optional[str], children: List[str]) -> List[str]:
        """
        Returns a list of candidate tags that are simultaneously compatible
        with the given parent and existing children.
        """
        candidates = self.rules.keys()
        valid_options = [
            tag
            for tag in candidates
            if self._is_substitution_candidate(
                tag, parent, children
            )  # pylint: disable=line-too-long
        ]
        return sorted(valid_options)

    def _is_substitution_candidate(
        self, tag: str, parent: Optional[str], children: List[str]
    ) -> bool:
        # Rule 1: Upwards Compatibility
        if parent:
            is_valid_child, _ = self.can_add_child(parent, tag)
            if not is_valid_child:
                return False
        elif tag not in self.root_allowed_tags:
            return False

        # Rule 2: Downwards Compatibility
        for child in children:
            if "👻" in child:
                continue
            is_valid_grandchild, _ = self.can_add_child(tag, child)
            if not is_valid_grandchild:
                return False

        return True

    # --- Métodos de Consulta (API Endpoints) ---

    def get_definition(self, tag: str) -> Dict[str, Any]:
        """Retorna la definición cruda para mostrar en el Inspector."""
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
        """Retorna lista ordenada de todas las etiquetas conocidas."""
        return sorted(self.rules.keys())

    def can_add_child(
        self, parent_tag: str, child_tag: str, strategy: str = "strict"
    ) -> Tuple[bool, str]:
        """¿Puede 'parent' contener a 'child'?"""
        if strategy == "lax":
            return True, "Lax Mode: Context check bypassed."

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
        Determina si un nodo puede cambiar su etiqueta (ej. de NP a VP).
        Retorna: Lista de etiquetas válidas para esa posición.
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
        """Retorna una lista de etiquetas padre que permiten al hijo dado."""
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
        Valida un nodo generando una traza detallada de las decisiones.
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

    def _validate_strict(
        self, node_label: str, children_labels: List[str], errors: List[str], trace: List[str]
    ):
        allowed = self.allowed_children.get(node_label, set())

        # 1. Illegal Children
        for child in children_labels:
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
            has_match = False
            for pattern in node_patterns:
                if self._contains_contiguous_subsequence(children_labels, pattern):
                    has_match = True
                    break

            if not has_match:
                msg = f"Strict: Node '{node_label}' does not contain any valid production pattern."
                errors.append(msg)
                trace.append(
                    f"❌ Pattern Check for '{node_label}': Children {children_labels} "
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
        # --- LAX MODE (Recursive Yield) ---
        # In lax mode, we check if the descendants satisfy the mandatory content derived from patterns.
        # Since we removed explicit 'mandatory', we use self.mandatory_children which is the intersection of patterns.
        scope_labels = (
            descendants_labels if descendants_labels is not None else children_labels
        )  # pylint: disable=line-too-long

        if children_labels:
            trace.append(
                "ℹ️ Lax Mode: Skipping 'Allowed Children' check to accommodate flattening."
            )  # pylint: disable=line-too-long

        mandatory_set = self.mandatory_children.get(node_label, set())

        # If intersection is empty (due to shortcuts), we can't enforce mandatory children strictly
        # in lax mode without more complex logic (e.g. checking if ANY pattern is satisfied by yield).
        # For now, we check the intersection if it exists.

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

        # If no mandatory children (e.g. leaf or shortcut-heavy node), we can't enforce presence via recursion  # pylint: disable=line-too-long
        if not target_mandatory:
            is_leaf = self.rules.get(target_type, {}).get("type") == "leaf"
            return not is_leaf

        # Check if ALL mandatory children of the target are present in context
        for sub_req in target_mandatory:
            if not self._check_yield_presence(sub_req, context_labels):
                return False

        return True

    def can_delete_child(
        self, parent_tag: str, child_tag: str, sibling_tags: List[str]
    ) -> Tuple[bool, str]:
        """
        Verifica si es legal borrar un hijo.
        """
        if not self.rules:
            return True, "Permissive Mode"

        # Check against mandatory set (intersection of patterns)
        mandatory_set = self.mandatory_children.get(parent_tag, set())

        # If the child to delete is in the mandatory set, and it's the last one of its kind...
        # But wait, mandatory_set is a SET of types.
        # If 'child_tag' is in mandatory_set, we must ensure it remains in sibling_tags.

        if child_tag in mandatory_set:
            if child_tag not in sibling_tags:
                return (
                    False,  # pylint: disable=line-too-long
                    f"Cannot delete '{child_tag}': Node '{parent_tag}' requires '{child_tag}' (Mandatory).",  # pylint: disable=line-too-long
                )

        return True, "OK"
