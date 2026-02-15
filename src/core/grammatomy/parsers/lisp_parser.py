import re
from pathlib import Path
from typing import List, Optional

import yaml
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


def _load_reserved_tags() -> set:
    """Load structural tags ONLY from hybrid_rules.yaml (the source of truth).

    This is the canonical grammar definition for the Grammatomy project.
    """
    fallback = set()

    try:
        # Path: parsers/lisp_parser.py -> parents[1] -> grammatomy/assets/rules/
        rules_path = Path(__file__).resolve().parents[1] / "assets" / "rules" / "hybrid_rules.yaml"
        if rules_path.exists():
            data = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
            ids = set()
            for node in data.get("nodes", []):
                nid = node.get("id")
                if nid:
                    ids.add(nid)
            return ids
    except Exception:
        pass

    # If YAML cannot be loaded, return empty set to signal an error
    # (rather than a silent fallback that might mask configuration issues)
    return fallback


# Master set of reserved tags used by the parser (structural tags + POS + punctuation)
RESERVED_TAGS = _load_reserved_tags()


def to_anytree(lisp_str: str) -> Optional[SyntaxNode]:
    """Parse a PTB/Lisp constituency string into an anytree SyntaxNode tree.

    This parser converts strings like "(S (NP (NNP Juan)) (VP (VBD vino)))"
    into a tree of SyntaxNode objects. It properly handles:
    - Structural nodes (S, NP, VP, etc. from RESERVED_TAGS)
    - Preterminal nodes (e.g. NNP, VBD) with terminal word children
    - Parentheses sanitization (-LRB- / -RRB-)
    """
    if not lisp_str or not lisp_str.strip():
        return None

    # Tokenize: split on parentheses and whitespace
    tokens = re.findall(r"(\(|\)|[^\s()]+)", lisp_str)
    stack: List[SyntaxNode] = []
    root: Optional[SyntaxNode] = None

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok == "(":
            # Next token should be a label
            if i + 1 < len(tokens):
                label = tokens[i + 1]
                is_reserved = label in RESERVED_TAGS or label.startswith("LINK-")

                if is_reserved:
                    # Create a structural node
                    node = SyntaxNode(label, label=label)
                    if stack:
                        node.parent = stack[-1]
                    else:
                        root = node
                    stack.append(node)
                    i += 2
                else:
                    # Non-reserved label in parens: it's a terminal attached to parent
                    # e.g. (Juan) where Juan is the terminal for the parent NP
                    if stack:
                        parent = stack[-1]
                        word = label.replace("-LRB-", "(").replace("-RRB-", ")")
                        # Only add if parent doesn't already have children
                        if not parent.children:
                            SyntaxNode(word, parent=parent, label=word, word=word)
                    i += 2
                    # Skip closing paren if it follows immediately
                    if i < len(tokens) and tokens[i] == ")":
                        i += 1
            else:
                i += 1

        elif tok == ")":
            if stack:
                stack.pop()
            i += 1

        else:
            # Bare word (terminal): attach to current parent
            word_text = tok.replace("-LRB-", "(").replace("-RRB-", ")")
            if stack:
                parent = stack[-1]
                # Only add if parent doesn't have children yet
                if not parent.children:
                    child = SyntaxNode(word_text, parent=parent, label=word_text, word=word_text)
                    # Mark preterminal: the parent's pos is its label
                    parent.pos = parent.label
                    # Also set the parent's word attribute
                    parent.word = word_text
            i += 1

    return root


class LispParser:
    """Wrapper class providing static methods for parsing PTB format strings."""

    @staticmethod
    def to_anytree(lisp_str: str) -> Optional[SyntaxNode]:
        """Alias for the module-level to_anytree function."""
        return to_anytree(lisp_str)


def from_ptb(lisp_str: str) -> Optional[SyntaxNode]:
    """Alias for to_anytree, for backward compatibility."""
    return to_anytree(lisp_str)
