from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml


class ValidationEngine:
    """
    Driven by 'rules_es.yaml', this engine validates syntactic trees
    supporting dual strategies: 'lax' (Neural) and 'strict' (AnCora).
    """

    def __init__(self, rules_path: str, strategy: str = "lax"):
        self.rules_path = Path(rules_path)
        self.strategy = strategy
        self.data = self._load_yaml()
        self.rules = self.data.get("nodes", {})
        self.transparency = self._load_transparency()

    def _load_yaml(self) -> Dict:
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {self.rules_path}")

        with open(self.rules_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_transparency(self) -> Dict[str, str]:
        """
        Loads the equivalence map (e.g., 'n' -> 'NOUN').
        Used to normalize tags.
        """
        mapping = {}
        raw_map = self.data.get("label_transparency", [])
        for entry in raw_map:
            canonical = entry["id"]
            for tag in entry["tags"]:
                mapping[tag] = canonical
            mapping[canonical] = canonical
        return mapping

    def _normalize_tag(self, tag: str) -> str:
        return self.transparency.get(tag, tag)

    def _get_children_config(
        self, node_label: str, strategy: str, key: str
    ) -> List[Any]:
        node_config = self.rules.get(node_label)
        if not node_config or not isinstance(node_config, dict):
            return []

        rules = node_config.get("rules", {})

        # For 'mandatory_children', we expect a list of lists (AND of ORs).
        # We don't merge sets here because order/structure matters for mandatory requirements.
        # We prioritize strategy-specific rules over 'all'.
        if key == "mandatory_children":
            return rules.get(strategy, {}).get(key, []) or rules.get("all", {}).get(
                key, []
            )
        else:
            # For allowed_children, we merge
            base = set(rules.get("all", {}).get(key, []))
            strat = set(rules.get(strategy, {}).get(key, []))
            return list(base | strat)

    def set_strategy(self, strategy: str):
        if strategy not in ["lax", "strict"]:
            raise ValueError("Strategy must be 'lax' or 'strict'")
        self.strategy = strategy

    def validate_node(
        self,
        node_label: str,
        children_labels: List[str],
        descendants_labels: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validates a node.
        Args:
            node_label: The label of the node being validated.
            children_labels: Direct children (for strict validation).
            descendants_labels: All descendants in the subtree (for lax validation).
        Returns (is_valid, error_messages, trace).
        """
        errors = []
        trace = []
        if node_label not in self.rules:
            return True, [], []

        # Check node type
        node_config = self.rules.get(node_label, {})
        node_type = node_config.get("type", "group")

        # If it's a leaf node (e.g. NOUN), it expects text children.
        # We don't validate children of leaves against allowed_children.
        if node_type == "leaf":
            return True, [], []

        if self.strategy == "strict":
            # Mandatory checks use all children (presence check only)
            mandatory_scope = children_labels
            # --- STRICT MODE (Classic) ---
            allowed = self._get_children_config(
                node_label, "strict", "allowed_children"
            )
            # Strict mandatory children: List of Lists [[Req1_Alt1, Req1_Alt2], [Req2...]]
            mandatory = self._get_children_config(
                node_label, "strict", "mandatory_children"
            )

            # 1. Illegal Children
            for child in children_labels:
                if child not in allowed:
                    msg = f"Strict: Node '{node_label}' cannot contain '{child}'."
                    errors.append(msg)
                    trace.append(
                        f"❌ Checked children of '{node_label}': Found illegal child '{child}'."
                    )
                    trace.append(f"   Allowed: {sorted(list(allowed))}")

            # 2. Mandatory Children
            present = set(mandatory_scope)
            for requirement_group in mandatory:
                # LOGIC:
                # The outer loop represents Syntagmatic obligations (AND). E.g., sp = Prep + Term.
                # The inner 'requirement_group' represents Paradigmatic alternatives (OR). E.g., Term = sn | S | ...
                if not any(alt in present for alt in requirement_group):
                    missing_desc = "/".join(requirement_group)
                    msg = f"Strict: Node '{node_label}' missing mandatory child of type [{missing_desc}]."
                    errors.append(msg)
                    trace.append(
                        f"❌ Checking mandatory children for '{node_label}': Missing [{missing_desc}]."
                    )
                    trace.append(f"   Current children: {list(present)}")

        elif self.strategy == "lax":
            # --- LAX MODE (Recursive Yield) ---
            # Requires descendants_labels to be passed. If not, falls back to children (shallow check).
            # For mandatory checks, we prefer valid_descendants > descendants > valid_children > children
            scope_labels = (
                descendants_labels
                if descendants_labels is not None
                else children_labels
            )

            mandatory_scope = scope_labels

            # 1. Illegal Children Check SKIPPED in Lax Mode.
            # Rationale: Flattening promotes grandchildren (e.g. ADJ, S) to direct children.
            # These are often not explicitly 'allowed' in the parent's strict definition,
            # but are legitimate artifacts of the flattening process.
            # In Lax mode, we focus ONLY on Mandatory Content (Yield).
            if children_labels:
                trace.append(
                    f"ℹ️ Lax Mode: Skipping 'Allowed Children' check to accommodate flattening."
                )

            # We use the STRICT definition of mandatory children as the "ideal" structure
            # that we check for presence (either direct or flattened).
            strict_mandatory = self._get_children_config(
                node_label, "strict", "mandatory_children"
            )

            for requirement_group in strict_mandatory:
                # requirement_group is [Alt1, Alt2...]. We need ONE of these to be satisfied.
                # Satisfaction means: Either the node is present, OR its mandatory content is present.

                satisfied = False
                for alt_type in requirement_group:
                    if self._check_yield_presence(alt_type, mandatory_scope):
                        satisfied = True
                        break

                if not satisfied:
                    missing_desc = "/".join(requirement_group)
                    msg = f"Lax: Node '{node_label}' is missing essential content (yield) for [{missing_desc}]."
                    errors.append(msg)
                    trace.append(
                        f"❌ Recursive Yield Check for '{node_label}': Could not find content for [{missing_desc}]."
                    )
                    trace.append(f"   Scope searched: {mandatory_scope}")

        return len(errors) == 0, errors, trace

    def validate_context(
        self, tag: str, parent_tag: Optional[str]
    ) -> Tuple[bool, List[str]]:
        """
        Checks if 'tag' is allowed under 'parent_tag'.
        Returns (is_valid, trace_log).
        """
        trace = []

        # 1. Root Check
        if not parent_tag:
            # We assume ROOT is the implicit parent context
            # Check if tag is allowed as a top-level node (e.g. S, ROOT)
            # For now, we allow S and ROOT.
            if tag in ["S", "ROOT", "sentence"]:
                return True, trace
            else:
                trace.append(f"❌ Context: '{tag}' cannot be a Root node.")
                return False, trace

        # 2. Lax Mode Bypass
        if self.strategy == "lax":
            trace.append(
                f"ℹ️ Lax Mode: Context check bypassed for '{tag}' in '{parent_tag}'."
            )
            return True, trace

        # 2. Parent Compatibility
        # Does parent allow this child?
        parent_allowed = self._get_children_config(
            parent_tag, self.strategy, "allowed_children"
        )

        if not parent_allowed:
            # If parent has no allowed children defined, it might be a terminal or undefined
            if parent_tag not in self.rules:
                trace.append(f"⚠️ Parent '{parent_tag}' is unknown in rules.")
            else:
                trace.append(
                    f"❌ Parent '{parent_tag}' does not allow any children (Terminal?)."
                )
            return False, trace

        if tag not in parent_allowed:
            trace.append(
                f"❌ Parent '{parent_tag}' is incompatible with child '{tag}'."
            )
            trace.append(
                f"   Allowed children for '{parent_tag}': {sorted(list(parent_allowed))}"
            )
            return False, trace

        return True, trace

    def _check_yield_presence(
        self, target_type: str, context_labels: List[str]
    ) -> bool:
        """
        Recursively checks if 'target_type' or its mandatory yield is present in 'context_labels'.
        """
        # 1. Direct Presence
        if target_type in context_labels:
            return True

        # 2. Recursive Yield Check (Flattening)
        # If target_type is missing, we check if its mandatory children are present.
        target_mandatory = self._get_children_config(
            target_type, "strict", "mandatory_children"
        )

        if not target_mandatory:
            # If the missing node has NO mandatory children (it's optional or empty),
            # then its absence is acceptable. We consider it "present in spirit".
            # Exception: If it's a leaf node (POS) and it's missing, it's definitely missing.
            # We assume leaf nodes don't have mandatory_children defined in YAML.
            is_leaf = self.rules.get(target_type, {}).get("type") == "leaf"
            return not is_leaf

        # If it has mandatory children, ALL of them (AND logic) must be satisfied.
        for sub_req_group in target_mandatory:
            # For this requirement group (OR logic), at least one alternative must be satisfied.
            group_satisfied = False
            for sub_alt in sub_req_group:
                if self._check_yield_presence(sub_alt, context_labels):
                    group_satisfied = True
                    break

            if not group_satisfied:
                return False  # One of the mandatory components of the missing node is also missing.

        return True

    def get_valid_parents(self, child_label: str) -> List[str]:
        # Re-implement using the cache if needed, or keep simple reverse index based on strict rules
        # For dropdowns, we usually want strict/canonical parents.
        valid = []
        for parent in self.rules:
            allowed = self._get_children_config(parent, "strict", "allowed_children")
            if child_label in allowed:
                valid.append(parent)
        return valid
