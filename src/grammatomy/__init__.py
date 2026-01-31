from typing import Optional, Dict, Any
from anytree import Node
from .engines.stanza_engine import StanzaEngine
from .engines.spacy_engine import SpacyEngine
from .exporters import to_json

__version__ = "0.1.0"

def get_syntax_tree(text: str, params: Optional[Dict[str, Any]] = None) -> Optional[Node]:
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

    if engine == "stanza":
        return StanzaEngine.get_tree(text, lang=lang, model_package=model_package, use_gpu=use_gpu)
    
    if engine == "spacy":
        return SpacyEngine.get_tree(text, lang=lang, model_package=model_package, use_gpu=use_gpu)
    
    raise NotImplementedError(f"Engine '{engine}' is not supported yet.")