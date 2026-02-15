from anytree import Node


def to_latex(node: Node) -> str:
    """
    Exports the tree starting at `node` to a LaTeX forest string.

    Args:
        node: The root node of the tree/subtree.

    Returns:
        str: LaTeX forest code (e.g., "\\begin{forest} [S [NP] [VP]] \\end{forest}").
    """

    def escape(s: str) -> str:
        # Escape special LaTeX characters
        # Forest uses brackets [] for structure, so we must escape them in labels
        return (
            s.replace("%", "\\%")
            .replace("$", "\\$")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace("[", "{[}")
            .replace("]", "{]}")
        )

    def recurse(n: Node, depth: int = 0) -> str:
        indent = "  " * depth
        label = escape(n.name)

        if n.is_leaf:
            return f"{indent}[{label}]"

        children_str = "\n".join(recurse(child, depth + 1) for child in n.children)
        return f"{indent}[{label}\n{children_str}\n{indent}]"

    return f"\\begin{{forest}}\n{recurse(node)}\n\\end{{forest}}"
