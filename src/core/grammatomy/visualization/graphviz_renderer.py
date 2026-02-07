import copy

from anytree import Node, PreOrderIter
from anytree.exporter import DotExporter

from ..glossary import TAG_MAP


def _enrich_tree_for_graphviz(root):
    """
    Creates a visual-only copy of the tree where 'word' attributes become explicit child nodes.
    """
    visual_root = copy.deepcopy(root)
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

    for node in PreOrderIter(visual_root):
        if hasattr(node, "word") and node.word:
            if node.name in punct_tags:
                setattr(node, "style_type", "punct")
            else:
                setattr(node, "style_type", "pos")

            word_node = Node(node.word, parent=node)
            setattr(word_node, "style_type", "word")
        else:
            setattr(node, "style_type", "phrasal")

    return visual_root


def _get_node_style(node):
    """Returns Graphviz attributes based on node style_type (Okabe-Ito Palette)."""
    style_map = {
        "word": (
            'shape=box, style="filled,rounded", fillcolor="#009E73", fontcolor="white"'
        ),
        "punct": (
            'shape=circle, style="filled", fillcolor="#999999", fontcolor="white"'
        ),
        "pos": (
            'shape=ellipse, style="filled", fillcolor="#56B4E9", fontcolor="black"'
        ),
        "phrasal": (
            'shape=box, style="filled", fillcolor="#E69F00", fontcolor="black"'
        ),
    }

    attrs = style_map.get(getattr(node, "style_type", "phrasal"), style_map["phrasal"])

    # Resolve Tooltip from Glossary
    label = node.name
    tooltip = label  # Default to label to avoid showing internal ID (e.g. 14023...)

    # Only add tooltips for non-terminal nodes (phrasal/pos), skip word/punct
    style_type = getattr(node, "style_type", "phrasal")
    if style_type not in ["word", "punct"]:
        if label in TAG_MAP["Phrasal"]:
            tooltip = TAG_MAP["Phrasal"][label]
        elif label in TAG_MAP["POS"]:
            tooltip = TAG_MAP["POS"][label]

    attrs += f', label="{node.name}", tooltip="{tooltip}", fontname="Sans-Serif"'
    return attrs


def get_graphviz_dot(root) -> str:
    """
    Generates the Graphviz DOT source code for the tree.
    """
    visual_root = _enrich_tree_for_graphviz(root)

    dot_lines = []
    # Use unique IDs to prevent merging
    exporter = DotExporter(
        visual_root, nodenamefunc=lambda n: str(id(n)), nodeattrfunc=_get_node_style
    )
    for line in exporter:
        dot_lines.append(line)

    return "".join(dot_lines)
