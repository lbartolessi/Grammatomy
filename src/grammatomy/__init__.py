from typing import Any, Dict, Optional

from .engines.spacy_engine import SpacyEngine
from .engines.stanza_engine import StanzaEngine
from .exporters import to_json, to_ptb
from .parsers import SyntaxNode, from_ptb

__version__ = "0.1.0"

__all__ = [
    "get_syntax_tree",
    "to_json",
    "to_ptb",
    "from_ptb",
    "StanzaEngine",
    "SpacyEngine",
    "SyntaxNode",
]


def get_syntax_tree(
    text: str, params: Optional[Dict[str, Any]] = None
) -> Optional[SyntaxNode]:  # type: ignore[name-defined]
    """
    Unified entry point for constituency parsing.

    Args:
        text: The input sentence.
        params: Configuration dict (e.g., {'lang': 'es', 'engine': 'stanza'}).
    """
    if params is None:
        params = {}

    engine = params.get("engine", "stanza")
    lang = params.get("lang", "es")
    model_package = params.get("model_package", "default")
    use_gpu = params.get("use_gpu", True)

    root = None

    if engine == "stanza":
        root = StanzaEngine.get_tree(
            text, lang=lang, model_package=model_package, use_gpu=use_gpu
        )

    elif engine == "spacy":
        root = SpacyEngine.get_tree(
            text, lang=lang, model_package=model_package, use_gpu=use_gpu
        )

    else:
        raise NotImplementedError(f"Engine '{engine}' is not supported yet.")

    return root
