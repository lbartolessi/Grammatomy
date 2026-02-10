"""
Linguistic Logic Module.

Implements geometric tree algorithms (C-Command) and Binding Theory principles.
Used for 'Strict Mode' semantic validation.
"""

from typing import List, Optional

from anytree import NodeMixin


def c_command(node_a: NodeMixin, node_b: NodeMixin) -> bool:
    """
    Determines if node_a c-commands node_b.
    Definition:
    1. A does not dominate B.
    2. B does not dominate A.
    3. The first branching node dominating A also dominates B.
    """
    if node_a is node_b:
        return False

    # 1 & 2: Domination check
    if node_b in node_a.descendants:
        return False
    if node_a in node_b.descendants:
        return False

    # 3. First branching parent
    current = node_a.parent
    while current:
        if len(current.children) > 1 or current.parent is None:
            # This is a branching node (or root)
            # Does it dominate B?
            return node_b in current.descendants
        current = current.parent

    return False


def get_local_domain(node: NodeMixin) -> Optional[NodeMixin]:
    """
    Finds the local domain (Governing Category) for a node.
    Simplification: The minimal S (Clause) or NP containing the node.
    """
    current = node.parent
    while current:
        # Check for Clause (S) or Noun Phrase (NP/sn)
        if current.name in ("S", "sn", "NP", "ROOT"):
            return current
        current = current.parent
    return None


def validate_binding_principles(root: NodeMixin) -> List[str]:
    """
    Audits the tree for violations of Binding Principles A, B, and C.
    Requires nodes to have 'index' and 'type' attributes.
    """
    violations = []
    # Collect all indexed nodes
    indexed_nodes = [n for n in root.descendants if hasattr(n, "index") and n.index]

    for node in indexed_nodes:
        node_type = getattr(node, "type", "unknown")
        local_domain = get_local_domain(node)

        # --- Principle A: Anaphor must be bound in local domain ---
        if node_type == "anaphor":
            is_bound = False
            if local_domain:
                # Search for antecedent in local domain
                potential_binders = [
                    n
                    for n in local_domain.descendants
                    if hasattr(n, "index") and n.index == node.index and n is not node
                ]
                for binder in potential_binders:
                    if c_command(binder, node):
                        is_bound = True
                        break

            if not is_bound:
                violations.append(
                    f"Principle A Violation: Anaphor '{node.name}' (index {node.index}) is not bound in its local domain."
                )

        # --- Principle B: Pronoun must be free in local domain ---
        elif node_type == "pronoun":
            if local_domain:
                potential_binders = [
                    n
                    for n in local_domain.descendants
                    if hasattr(n, "index") and n.index == node.index and n is not node
                ]
                for binder in potential_binders:
                    if c_command(binder, node):
                        violations.append(
                            f"Principle B Violation: Pronoun '{node.name}' (index {node.index}) is bound by '{binder.name}' in its local domain."
                        )
                        break

        # --- Principle C: R-expression must be free everywhere ---
        elif node_type == "r-expression":
            # Search entire tree for binders
            potential_binders = [
                n for n in indexed_nodes if n.index == node.index and n is not node
            ]
            for binder in potential_binders:
                if c_command(binder, node):
                    violations.append(
                        f"Principle C Violation: R-expression '{node.name}' (index {node.index}) is bound by '{binder.name}'."
                    )
                    break

    return violations
