import copy
from anytree import Node, PreOrderIter
from anytree.exporter import DotExporter

def _enrich_tree_for_graphviz(root):
    """
    Creates a visual-only copy of the tree where 'word' attributes become explicit child nodes.
    """
    visual_root = copy.deepcopy(root)
    punct_tags = [".", ",", ":", ";", "!", "?", "...", "(", ")", "``", "''", "--", "-", "«", "»"]

    for node in list(PreOrderIter(visual_root)):
        if hasattr(node, "word") and node.word:
            if node.name in punct_tags:
                node.style_type = "punct"
            else:
                node.style_type = "pos"
            
            word_node = Node(node.word, parent=node)
            word_node.style_type = "word"
        else:
            node.style_type = "phrasal"
            
    return visual_root

def _get_node_style(node):
    """Returns Graphviz attributes based on node style_type (Okabe-Ito Palette)."""
    style_map = {
        "word":    ('shape=box, style="filled,rounded", fillcolor="#009E73", fontcolor="white"'),
        "punct":   ('shape=circle, style="filled", fillcolor="#999999", fontcolor="white"'),
        "pos":     ('shape=ellipse, style="filled", fillcolor="#56B4E9", fontcolor="black"'),
        "phrasal": ('shape=box, style="filled", fillcolor="#E69F00", fontcolor="black"'),
    }
    
    attrs = style_map.get(getattr(node, "style_type", "phrasal"), style_map["phrasal"])
    # Add label explicitly and disable tooltip
    attrs += f', label="{node.name}", tooltip=" ", fontname="Sans-Serif"'
    return attrs

def get_graphviz_dot(root) -> str:
    """
    Generates the Graphviz DOT source code for the tree.
    """
    visual_root = _enrich_tree_for_graphviz(root)
    
    dot_lines = []
    # Use unique IDs to prevent merging
    exporter = DotExporter(
        visual_root, 
        nodenamefunc=lambda n: str(id(n)), 
        nodeattrfunc=_get_node_style
    )
    for line in exporter:
        dot_lines.append(line)
        
    return "".join(dot_lines)