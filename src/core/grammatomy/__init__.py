"""
Grammatomy Core Library.

This package provides the core linguistic processing logic for the Grammatomy suite,
including parsing engines, data structure validation, and various output renderers.

Example:
    >>> from grammatomy import Grammar
    >>> grammar = Grammar(engine="stanza", lang="es")
    >>> tree = grammar.parse("El perro persigue al gato.")
    >>> print(tree.render_ascii())

Attributes:
    __version__ (str): The current version of the library.
"""

__version__ = "0.2.0"

from .config import config
from .engines.spacy_engine import SpacyEngine
from .engines.stanza_engine import StanzaEngine
from .exporters.json_exporter import to_json
from .exporters.ptb_exporter import to_ptb
from .grammar import Grammar, get_syntax_tree
from .parsers.lisp_parser import LispParser
from .visualization.ascii_renderer import render_ascii_colored
from .visualization.graphviz_renderer import get_graphviz_dot
from .visualization.json_renderer import render_json_colored
from .visualization.lisp_renderer import render_lisp_colored

# Alias for backward compatibility and convenience
from_ptb = LispParser.to_anytree

__all__ = [
    "Grammar",
    "get_syntax_tree",
    "config",
    "SpacyEngine",
    "StanzaEngine",
    "LispParser",
    "to_json",
    "to_ptb",
    "from_ptb",
    "render_ascii_colored",
    "get_graphviz_dot",
    "render_json_colored",
    "render_lisp_colored",
]
