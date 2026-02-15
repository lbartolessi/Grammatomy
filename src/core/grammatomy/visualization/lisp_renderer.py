"""
LISP/S-Expression Renderer Module.

Renders the tree in the classic LISP-style parenthesized notation (S-expressions),
commonly used in linguistics (e.g., Penn Treebank format).
"""

from anytree import Node


def render_lisp_colored(node: Node) -> str:
    """
    Renders the tree as a colored LISP S-expression (HTML format).

    Args:
        node: The root node of the tree.

    Returns:
        An HTML string representing the tree in LISP notation with syntax highlighting.
    """
    punct_tags = [".", ",", ":", ";", "!", "?", "...", "(", ")", "``", "''", "--", "-", "«", "»"]

    def _recursive_html(current_node, level=0):
        indent = "&nbsp;" * (level * 4)
        html = ""

        # Determine style
        label = current_node.name
        is_punct = label in punct_tags

        # Open parenthesis line
        html += f"<div>{indent}<span class='tree-connector'>(</span>"

        # Label
        style_class = (
            "style-punct"
            if is_punct
            else (
                "style-pos"
                if hasattr(current_node, "word") and current_node.word
                else "style-phrasal"
            )
        )
        html += f"<span class='{style_class}'>{label}</span>"

        # Word (Leaf)
        if hasattr(current_node, "word") and current_node.word:
            html += f" <span class='style-word'>\"{current_node.word}\"</span>"
            html += f"<span class='tree-connector'>)</span></div>"
        else:
            # Children (Recursive)
            if current_node.children:
                # We force a newline for children to ensure "pretty printing" vertical alignment
                for child in current_node.children:
                    html += _recursive_html(child, level + 1)
                html += f"<div>{indent}<span class='tree-connector'>)</span></div>"
            else:
                # Empty node case
                html += f"<span class='tree-connector'>)</span></div>"

        return html

    return (
        f"<div style='font-family: monospace; white-space: nowrap;'>{_recursive_html(node)}</div>"
    )
