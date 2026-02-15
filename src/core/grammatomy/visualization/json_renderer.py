"""
JSON Renderer Module.

Renders the tree structure as a syntax-highlighted JSON string (HTML format),
useful for debugging and inspecting the raw data structure in the UI.
"""

import json

from ..exporters import to_json


def render_json_colored(root) -> str:
    """
    Renders the tree as a colored JSON-like HTML structure.

    Args:
        root: The root node of the tree.

    Returns:
        An HTML string representing the tree in JSON format with syntax highlighting.
    """
    json_str = to_json(root)
    data = json.loads(json_str)

    def _recursive_html(node_dict, indent=0):
        html = ""
        padding = "&nbsp;" * (indent * 4)

        # Determine style based on content
        label = node_dict.get("name", "UNKNOWN")
        word = node_dict.get("word")

        punct_tags = [
            ".",
            ",",
            ":",
            ";",
            "!",
            "?",
            "...",
            "(",
            ")",
            "``",
            "''",
            "--",
            "-",
            "«",
            "»",
        ]

        if word:
            style_class = "style-punct" if label in punct_tags else "style-pos"
        else:
            style_class = "style-phrasal"

        # Open object
        html += f"<div>{padding}{{</div>"

        # Label
        html += f"<div>{padding}&nbsp;&nbsp;&nbsp;&nbsp;<span class='tree-connector'>\"label\":</span> <span class='{style_class}'>\"{label}\"</span>,</div>"

        # Word (if exists)
        if word:
            html += f"<div>{padding}&nbsp;&nbsp;&nbsp;&nbsp;<span class='tree-connector'>\"word\":</span> <span class='style-word'>\"{word}\"</span>,</div>"

        # Children
        if "children" in node_dict and node_dict["children"]:
            html += f"<div>{padding}&nbsp;&nbsp;&nbsp;&nbsp;<span class='tree-connector'>\"children\":</span> [</div>"
            for child in node_dict["children"]:
                html += _recursive_html(child, indent + 2)
            html += f"<div>{padding}&nbsp;&nbsp;&nbsp;&nbsp;],</div>"

        # Close object
        html += f"<div>{padding}}},</div>"
        return html

    return f"<div style='font-family: monospace;'>{_recursive_html(data)}</div>"
