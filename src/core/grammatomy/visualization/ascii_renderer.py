"""
ASCII Renderer Module.

Provides functionality to render syntactic trees as colored ASCII/HTML representations,
suitable for console output or simple web displays.
"""

from anytree import RenderTree


def render_ascii_colored(root) -> str:
    """
    Renders the tree structure in a colored ASCII format (HTML-safe).

    Args:
        root: The root node of the tree to render.

    Returns:
        A string containing the HTML representation of the ASCII tree.
    """
    punct_tags = [".", ",", ":", ";", "!", "?", "...", "(", ")", "``", "''", "--", "-", "«", "»"]

    html_lines = []
    for pre, _, node in RenderTree(root):
        # Escape HTML characters in pre and node content
        safe_pre = pre.replace("<", "&lt;").replace(">", "&gt;")

        line_content = f"<span class='tree-connector'>{safe_pre}</span>"

        label = node.name

        # Determine style for the node label
        if hasattr(node, "word") and node.word:
            style_class = "style-punct" if label in punct_tags else "style-pos"
        else:
            style_class = "style-phrasal"

        line_content += f"<span class='{style_class}'>{label}</span>"

        if hasattr(node, "word") and node.word:
            line_content += f": <span class='style-word'>\"{node.word}\"</span>"

        html_lines.append(line_content)

    return "\n".join(html_lines)
