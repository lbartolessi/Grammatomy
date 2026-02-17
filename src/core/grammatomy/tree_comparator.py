"""
Tree Comparator Module.

Provides utilities to compare two AnyTree structures node by node,
reporting structural and content differences for validation and testing.
"""

from itertools import zip_longest
from typing import List, Optional

from anytree import Node

from core.grammatomy.parsers.lisp_parser import LispParser


class TreeComparator:
    """
    Static utility for deep tree comparison.
    """

    @staticmethod
    def compare_ptb(ptb1: str, ptb2: str) -> List[str]:
        """
        Parses two PTB strings and compares the resulting trees.
        """
        parser = LispParser()
        # Wrap in VIRTUAL_ROOT to handle forests consistently
        t1 = parser.to_anytree(f"(VIRTUAL_ROOT {ptb1})")
        t2 = parser.to_anytree(f"(VIRTUAL_ROOT {ptb2})")
        return TreeComparator.compare(t1, t2)

    @staticmethod
    def compare(tree1: Optional[Node], tree2: Optional[Node]) -> List[str]:
        """
        Compares two trees recursively.
        Returns a list of strings describing the differences found.
        If the list is empty, the trees are identical.
        """
        diffs = []
        # Handle case where roots might be None
        if tree1 is None and tree2 is None:
            return []
        if tree1 is None:
            return ["Root of Tree 1 is None"]
        if tree2 is None:
            return ["Root of Tree 2 is None"]

        TreeComparator._recurse(tree1, tree2, "root", diffs)
        return diffs

    @staticmethod
    def _recurse(n1: Optional[Node], n2: Optional[Node], path: str, diffs: List[str]):
        if n1 is None:
            n2_name = getattr(n2, "name", "Unknown") if n2 else "Unknown"
            diffs.append(f"[{path}] Missing in Tree 1 (Tree 2 has '{n2_name}')")
            return
        if n2 is None:
            n1_name = getattr(n1, "name", "Unknown") if n1 else "Unknown"
            diffs.append(f"[{path}] Missing in Tree 2 (Tree 1 has '{n1_name}')")
            return

        if n1.name != n2.name:
            diffs.append(f"[{path}] Label mismatch: '{n1.name}' != '{n2.name}'")

        # Compare Children
        for i, (c1, c2) in enumerate(zip_longest(n1.children, n2.children)):
            TreeComparator._recurse(c1, c2, f"{path}.{i}", diffs)
