from typing import List, Optional

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
        raw_lisp=None,
        **kwargs,
    ):
        super().__init__(name, parent, children, **kwargs)
        self.label = label if label is not None else name
        self.word = word
        self.pos = pos
        self.raw_lisp = raw_lisp


def _process_token(
    token: str, stack: List[SyntaxNode], tokens: List[str], index: int
) -> int:
    """Processes a single token and updates the stack."""
    if token == "(":
        # Look ahead for the label
        if index + 1 < len(tokens):
            label = tokens[index + 1]
            node = SyntaxNode(label, label=label)
            if stack:
                node.parent = stack[-1]
            stack.append(node)
            return index + 1  # Skip the label we just consumed
    elif token == ")":
        if stack:
            stack.pop()
    else:
        # It is a leaf content (terminal). Reverse sanitization
        word_text = token.replace("-LRB-", "(").replace("-RRB-", ")")
        if stack:
            parent_node = stack[-1]
            # 1. Create structural leaf for export/traversal compatibility
            SyntaxNode(word_text, parent=parent_node)
            # 2. Set attributes on the parent POS node
            parent_node.word = word_text
            # Heuristic: if the parent has a label, that label is likely the POS
            parent_node.pos = parent_node.label

    return index


def from_ptb(ptb_string: str) -> SyntaxNode:
    """
    Parses a Penn Treebank (S-expression) string into an anytree Node structure.

    Reverses the logic of `to_ptb`, including parenthesis desanitization.

    Args:
        ptb_string: The PTB formatted string (e.g., "(S (NP Juan))").

    Returns:
        SyntaxNode: The root node of the constructed tree.
    """
    if not ptb_string or not ptb_string.strip():
        raise ValueError("Input PTB string is empty")

    # Normalize spaces around parentheses to facilitate tokenization
    # We assume standard PTB format where structure parens are separate.
    normalized = ptb_string.replace("(", " ( ").replace(")", " ) ")
    tokens = normalized.split()

    # Root will be the first node created
    stack: List[SyntaxNode] = []
    root_ref: List[SyntaxNode] = []  # Mutable container to capture root

    i = 0
    while i < len(tokens):
        # Capture root on first node creation
        if tokens[i] == "(" and not root_ref and i + 1 < len(tokens):
            # We can't easily capture it inside _process_token without more complexity
            # So we peek here.
            pass

        new_index = _process_token(tokens[i], stack, tokens, i)

        # If we just created the first node (stack size 1) and root_ref is empty
        if len(stack) == 1 and not root_ref:
            root_ref.append(stack[0])

        i = new_index + 1

    if not root_ref:
        raise ValueError("Failed to parse PTB string: No root found.")

    return root_ref[0]


class LispParser:
    """
    Legacy wrapper for backward compatibility with existing tests.
    Delegates logic to the functional `from_ptb` implementation.
    """

    @staticmethod
    def to_anytree(lisp_str: str) -> Optional[SyntaxNode]:
        try:
            return from_ptb(lisp_str)
        except ValueError:
            return None
