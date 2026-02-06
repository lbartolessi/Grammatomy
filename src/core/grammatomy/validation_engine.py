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
        self._reverse_index: Dict[str, Set[str]] = (
            {}
        )  # Derived index: Child -> Valid Parents
        self.terminal_parents: Set[str] = (
            set()
        )  # Tags that allow terminals (empty allowed list)
        self.root_allowed_tags: Set[str] = set()

        self._load_rules()
        self._validate_consistency()
        self._initialized = True

    def _load_rules(self):
        if not self.rules_path.exists():
            logger.error(f"Rules file not found: {self.rules_path}")
            print(f"❌ Rules file not found: {self.rules_path}")
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.error(f"Rules file is empty or invalid YAML: {self.rules_path}")
                return

            # Language Check: Ensure rules match the requested language
            config = data.get("tree_config", {})
            rule_lang = config.get("language")

            # If language is specified and doesn't match, skip loading (Permissive Mode)
            if rule_lang and rule_lang.lower() != self.lang:
                logger.warning(
                    f"Rules language '{rule_lang}' does not match requested '{self.lang}'. Enabling Permissive Mode."
                )
                return

            # Parse new list-based structure
            raw_nodes = data.get("nodes", [])
            self.rules = {}

            for node in raw_nodes:
                tag = node["id"]
                self.rules[tag] = node

                # Flatten allowed children
                children_config = node.get("allowed_children", {})
                if children_config:
                    obligatory = children_config.get("mandatory", []) or []
                    optional = children_config.get("optional", []) or []
                    self.allowed_children[tag] = set(obligatory + optional)
                    self.mandatory_children[tag] = set(obligatory)
                else:
                    self.allowed_children[tag] = set()
                    self.mandatory_children[tag] = set()

                self.allowed_parents[tag] = set(node.get("allowed_parents", []) or [])

                if not self.allowed_children[tag]:
                    self.terminal_parents.add(tag)

                if node.get("root_allowed", False):
                    self.root_allowed_tags.add(tag)

                # Register functional variants as aliases to the same rule
                for variant in node.get("functional_variants", []) or []:
                    print(f"   🔗 Registering variant: '{variant}' -> '{tag}'")
                    self.rules[variant] = node
                    self.allowed_children[variant] = self.allowed_children[tag]
                    self.allowed_parents[variant] = self.allowed_parents[tag]
                    self.mandatory_children[variant] = self.mandatory_children[tag]
                    if tag in self.root_allowed_tags:
                        self.root_allowed_tags.add(variant)

            # Build reverse index from 'allowed' lists for O(1) lookups
            for tag, children in self.allowed_children.items():
                for child in children:
                    if child not in self._reverse_index:
                        self._reverse_index[child] = set()
                    self._reverse_index[child].add(tag)

            logger.info(
                f"ValidationEngine loaded {len(self.rules)} rules from {self.rules_path}"
            )
            print(
                f"✅ ValidationEngine loaded {len(self.rules)} rules from {self.rules_path}"
            )
            print(f"   🔑 Sample keys: {list(self.rules.keys())[:5]}")

        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            raise

    def _validate_consistency(self):
        """Verifica la coherencia bidireccional de las reglas al inicio."""
        inconsistencies = []
        for parent, children_set in self.allowed_children.items():
            for child in children_set:
                # Si el hijo tiene reglas definidas, debe listar al padre como permitido
                if child in self.allowed_parents:
                    if parent not in self.allowed_parents[child]:
                        inconsistencies.append(
                            f"Inconsistency: '{parent}' allows '{child}', but '{child}' does not allow '{parent}'."
                        )

        if inconsistencies:
            logger.warning(
                f"Validation Rules Inconsistencies found for {self.lang}: {inconsistencies}"
            )

    def get_valid_substitutions(
        self, parent: Optional[str], children: List[str]
    ) -> List[str]:
        """
        Returns a list of candidate tags that are simultaneously compatible
        with the given parent and existing children.
        """
        # 1. Get universe of tags
        candidates = list(self.rules.keys())

        valid_options = []

        for tag in candidates:
            # Rule 1: Upwards Compatibility
            # Does the current parent allow 'tag' as a child?
            if parent:
                is_valid_child, _ = self.can_add_child(parent, tag)
                if not is_valid_child:
                    continue
            else:
                # Rule 1.1: Root Compatibility
                # If no parent, is this tag allowed to be a root?
                if tag not in self.root_allowed_tags:
                    continue

            # Rule 2: Downwards Compatibility
            # Does the candidate 'tag' allow ALL current children?
            children_compatible = True
            for child in children:
                if "👻" in child:
                    continue
                is_valid_grandchild, _ = self.can_add_child(tag, child)
                if not is_valid_grandchild:
                    children_compatible = False
                    break

            if children_compatible:
                valid_options.append(tag)

        return sorted(valid_options)

    # --- Métodos de Consulta (API Endpoints) ---

    def get_definition(self, tag: str) -> Dict[str, Any]:
        """Retorna la definición cruda para mostrar en el Inspector."""
        # Self-healing: If rules are empty (e.g. failed load on startup), try reloading
        if not self.rules:
            print("⚠️ Rules registry is empty. Attempting lazy reload...")
            self._load_rules()

        val = self.rules.get(tag, {})
        if not val:
            # Debug probe: Print exact mismatch details
            print(
                f"⚠️ MISSING DEFINITION: Requested tag='{tag}' (len={len(tag)}). "
                f"Available keys sample: {list(self.rules.keys())[:5]}"
            )
        return val

    def get_all_tags(self) -> List[str]:
        """Retorna lista ordenada de todas las etiquetas conocidas."""
        return sorted(list(self.rules.keys()))

    def can_add_child(self, parent_tag: str, child_tag: str) -> Tuple[bool, str]:
        """¿Puede 'parent' contener a 'child'?"""
        if parent_tag not in self.allowed_children:
            # Permissive Mode: If we have no rules loaded, allow everything
            if not self.rules:
                return True, "Permissive Mode (No rules)"

            # Si no hay reglas, asumimos terminal o restrictivo por defecto
            return False, f"Node '{parent_tag}' is a terminal or has no rules defined."

        if child_tag not in self.allowed_children[parent_tag]:
            # Exception: If parent expects terminal (empty allowed) and child is NOT a known tag
            # we assume child is a text leaf.
            if not self.allowed_children[parent_tag] and child_tag not in self.rules:
                return True, "OK"

            return (
                False,
                f"'{parent_tag}' does not allow '{child_tag}'. Allowed: {sorted(list(self.allowed_children[parent_tag]))}",
            )

        return True, "OK"

    def can_convert_node(
        self,
        current_tag: str,
        ancestor_tags: List[str],
        current_children_tags: List[str],
    ) -> List[str]:
        """
        Determina si un nodo puede cambiar su etiqueta (ej. de NP a VP).
        Retorna: Lista de etiquetas válidas para esa posición.
        Lógica Ascendente: Se permite si ALGÚN ancestro está en la lista de padres permitidos.
        """
        candidates = set(self.rules.keys())
        ancestors_set = set(ancestor_tags)

        # 1. Filter candidates based on Ancestor Compatibility (Upwards)
        if ancestors_set:
            # Keep candidates where Intersection(AllowedParents, Ancestors) is NOT empty
            candidates = {
                tag
                for tag in candidates
                if not self.allowed_parents.get(tag, set()).isdisjoint(ancestors_set)
            }
        else:
            # No parent (Root context) -> All tags are candidates initially
            # (Or restrict to ROOT allowed tags if we had a meta-root)
            candidates = set(self.rules.keys())

        # 2. Filter candidates that allow ALL current children
        for child in current_children_tags:
            # Get set of parents that allow this child
            if child in self.rules:
                valid_parents_for_child = self._reverse_index.get(child, set())
            else:
                # Child is a terminal (word) -> Valid parents are those that accept terminals
                valid_parents_for_child = self.terminal_parents
            # Intersection: Candidate must be a valid parent for this child
            candidates &= valid_parents_for_child

        return sorted(list(candidates))

    def validate_requirements(
        self, tag: str, descendant_tags: List[str]
    ) -> Tuple[bool, str]:
        """
        Valida si un nodo cumple sus requisitos obligatorios buscando en TODOS sus descendientes.
        Lógica: 'obligatorios' significa que AL MENOS UNO de esos tipos debe existir en el subárbol.
        """
        if not self.rules:
            return True, "Permissive Mode"

        mandatory = self.mandatory_children.get(tag, set())
        if not mandatory:
            return True, "OK"

        descendants = set(descendant_tags)
        # Check if disjoint: If intersection is empty, requirement is not met.
        if mandatory.isdisjoint(descendants):
            return (
                False,
                f"Missing required structure. Must contain at least one of: {sorted(list(mandatory))}",
            )

        return True, "OK"

    def can_delete_child(
        self, parent_tag: str, child_tag: str, sibling_tags: List[str]
    ) -> Tuple[bool, str]:
        """
        Verifica si es legal borrar un hijo, asegurando que no sea obligatorio y único.
        sibling_tags: Lista de etiquetas de los hermanos RESTANTES (excluyendo el que se borra).
        """
        if not self.rules:
            return True, "Permissive Mode"

        if parent_tag in self.mandatory_children:
            if child_tag in self.mandatory_children[parent_tag]:
                # Si es obligatorio, debe haber al menos otro hermano del mismo tipo
                if child_tag not in sibling_tags:
                    return (
                        False,
                        f"Cannot delete: '{child_tag}' is mandatory for '{parent_tag}' and no other sibling exists.",
                    )

        return True, "OK"
