import re
from typing import Optional
from anytree import Node


class SyntaxNode(Node):
    """Typed wrapper around anytree.Node for static analysis support."""

    def __init__(
        self,
        name,
        parent=None,
        children=None,
        label=None,
        word=None,
        pos=None,
        **kwargs
    ):
        super().__init__(name, parent, children, **kwargs)
        self.label = label
        self.word = word
        self.pos = pos


class LispParser:
    """
    Universal converter from Penn Treebank (LISP-style) strings to AnyTree Nodes.
    """

    @staticmethod
    def _create_pending_node(stack: list[SyntaxNode]) -> SyntaxNode:
        node = SyntaxNode("PENDING", label=None, word=None, pos=None)
        if stack:
            node.parent = stack[-1]
        return node

    @staticmethod
    def _process_content(stack: list[SyntaxNode], token: str) -> None:
        if stack:
            current_node = stack[-1]
            if current_node.name == "PENDING":
                current_node.name = token
                current_node.label = token
            else:
                current_node.word = token
                current_node.pos = current_node.label

    @staticmethod
    def to_anytree(lisp_str: str) -> Optional[SyntaxNode]:
        """
        Parses a LISP-style constituent string into an anytree Node hierarchy.

        Args:
            lisp_str: String in PTB format, e.g., "(S (NP (NNP Juan)) (VP (VBD vino)))"

        Returns:
            The root Node of the tree.
        """
        if not lisp_str or not lisp_str.strip():
            return None

        # Normalize whitespace
        clean_str = re.sub(r"\s+", " ", lisp_str).strip()

        # Tokenize: ensure parens are separated, then split
        # Note: PTB usually escapes parens in text as -LRB- / -RRB-, so this is safe.
        tokens = clean_str.replace("(", " ( ").replace(")", " ) ").split()

        stack = []
        root = None

        for token in tokens:
            if token == "(":
                node = LispParser._create_pending_node(stack)
                if not stack:
                    root = node
                stack.append(node)

            elif token == ")":
                if stack:
                    stack.pop()

            else:
                LispParser._process_content(stack, token)

        return root
