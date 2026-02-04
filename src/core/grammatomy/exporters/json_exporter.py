from typing import Any
from anytree import Node
from anytree.exporter import JsonExporter

def to_json(node: Node, indent: int = 2, **kwargs: Any) -> str:
    """
    Exports the tree starting at `node` to a JSON string.
    
    Args:
        node: The root node of the tree/subtree.
        indent: Indentation level for pretty-printing (default: 2).
        **kwargs: Additional arguments passed to anytree.exporter.JsonExporter.
    
    Returns:
        str: JSON representation of the tree.
    """
    exporter = JsonExporter(indent=indent, **kwargs)
    return exporter.export(node)