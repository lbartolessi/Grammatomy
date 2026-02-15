"""
Graphviz Renderer Module.

Generates DOT code for visualizing syntactic trees using Graphviz.
Supports custom styling for phrasal nodes, POS tags, and terminals.
"""

from anytree import Node
from anytree.exporter import DotExporter

from ..glossary import TAG_MAP

# Style Constants matching Frontend (Cytoscape)
STYLE_PHRASAL = {
    "shape": "box",
    "style": "filled,rounded",
    "fillcolor": "#E69F00",  # Orange
    "fontname": "Roboto Mono, Arial",
    "fontsize": "12",
    "fontcolor": "#161616",
    "penwidth": "2",
}

STYLE_POS = {
    "shape": "box",
    "style": "filled",
    "fillcolor": "#56B4E9",  # Sky Blue
    "fontname": "Roboto Mono, Arial",
    "fontsize": "12",
    "fontcolor": "#161616",
    "penwidth": "0",
}

STYLE_LEAF = {
    "shape": "box",
    "style": "filled",
    "fillcolor": "#009E73",  # Green
    "fontname": "Roboto Mono, Arial",
    "fontsize": "12",
    "fontcolor": "#F4F4F4",  # White text
    "penwidth": "0",
}

STYLE_LINK = {
    "shape": "ellipse",
    "style": "filled",
    "fillcolor": "#0072B2",  # Dark Blue
    "fontname": "Roboto Mono, Arial",
    "fontsize": "12",
    "fontcolor": "#FFFFFF",
    "penwidth": "1",
}

STYLE_PUNCT = {
    "shape": "circle",
    "style": "filled",
    "fillcolor": "#999999",
    "fontname": "Roboto Mono, Arial",
    "fontsize": "12",
    "fontcolor": "#FFFFFF",
    "penwidth": "0",
}

PUNCT_TAGS = {
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
    "$",
    "#",
    "PUNCT",
}


def get_graphviz_dot(root) -> str:
    """
    Generates a styled Graphviz DOT string representation of the tree.

    Args:
        root: The root node of the syntax tree.

    Returns:
        A string containing the DOT graph definition.
    """

    def nodeattrfunc(node):
        # Determine node type and style
        if node.name.startswith("LINK-"):
            style = STYLE_LINK
        elif node.is_leaf:
            # It's a terminal word
            if node.parent and node.parent.name in PUNCT_TAGS:
                style = STYLE_PUNCT
            else:
                style = STYLE_LEAF
        else:
            # It's a non-terminal.
            # Heuristic: A node is POS if all its children are leaves.
            is_pos = all(child.is_leaf for child in node.children)

            if is_pos:
                if node.name in PUNCT_TAGS:
                    style = STYLE_PUNCT
                else:
                    style = STYLE_POS
            else:
                style = STYLE_PHRASAL

        attrs = [f'{k}="{v}"' for k, v in style.items()]

        # Escape label for DOT
        label = node.name.replace('"', '\\"')
        attrs.append(f'label="{label}"')

        # Add tooltip if available
        tooltip = label
        if node.name in TAG_MAP["Phrasal"]:
            tooltip = TAG_MAP["Phrasal"][node.name]
        elif node.name in TAG_MAP["POS"]:
            tooltip = TAG_MAP["POS"][node.name]
        attrs.append(f'tooltip="{tooltip}"')

        return ",".join(attrs)

    def edgeattrfunc(node, child):
        return 'dir="none"'  # Undirected edges for constituency trees

    dot_lines = []
    # Use unique IDs to prevent merging
    exporter = DotExporter(
        root,
        nodenamefunc=lambda n: str(id(n)),
        nodeattrfunc=nodeattrfunc,
        edgeattrfunc=edgeattrfunc,
        options=['rankdir="TB"'],
    )
    for line in exporter:
        dot_lines.append(line)

    return "".join(dot_lines)
