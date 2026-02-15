from anytree import Node


class PtbExporter:
    """
    Exporter for Penn Treebank format.
    Wraps the functional to_ptb logic for object-oriented usage.
    """

    def export(self, node: Node) -> str:
        return to_ptb(node)


def to_ptb(node: Node) -> str:
    """
    Exports the tree starting at `node` to a Penn Treebank (S-expression) string.

    This format is ideal for database storage and serialization as it is
    compact and standard in NLP.

    Args:
        node: The root node of the tree/subtree.

    Returns:
        str: PTB representation (e.g., "(S (NP (N Juan)) (VP (V duerme)))").
    """
    if node.is_leaf:
        # Sanitize parentheses to avoid breaking the S-expression structure
        # Standard PTB convention: ( -> -LRB-, ) -> -RRB-
        return node.name.replace("(", "-LRB-").replace(")", "-RRB-")

    children_str = " ".join(to_ptb(child) for child in node.children)
    return f"({node.name} {children_str})"
