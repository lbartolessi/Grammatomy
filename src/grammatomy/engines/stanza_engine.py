import gc
from pathlib import Path
from typing import Any, Dict, Optional

import stanza
import torch

from ..parsers.lisp_parser import LispParser, SyntaxNode

# Define local models path relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STANZA_DIR = str(PROJECT_ROOT / "models" / "stanza")


class StanzaEngine:
    """
    Adapter for Stanford Stanza NLP library.
    Handles model loading and constituency parsing.
    """

    # Cache for loaded pipelines to avoid reloading heavy models
    _pipelines: Dict[str, stanza.Pipeline] = {}

    @classmethod
    def clear_cache(cls):
        """Clears the pipeline cache and forces garbage collection to free VRAM."""
        # Explicitly delete pipelines to ensure reference counts drop
        for pipeline in cls._pipelines.values():
            del pipeline
        cls._pipelines.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @classmethod
    def get_tree(
        cls,
        text: str,
        lang: str = "es",
        model_package: str = "default",
        use_gpu: bool = True,
    ) -> Optional[SyntaxNode]:
        """
        Generates a constituency tree using Stanza.

        Args:
            text: The input sentence(s).
            lang: Language code (es, en, fr, etc.).
            model_package: Specific Stanza package/model to use.
            use_gpu: Whether to try using GPU (default: True).

        Returns:
            Root Node of the parsed tree (for the first sentence).
        """
        # Default model override for Spanish: Prefer BERT over CharLM/Default
        if lang == "es" and model_package == "default":
            model_package = "combined_bertin-roberta"

        cache_key = f"{lang}_{model_package}_{use_gpu}"

        if cache_key not in cls._pipelines:
            # Ensure models are downloaded
            # 1. Determine processors based on language
            processors = ["tokenize"]
            if lang not in ["en", "zh", "zh-hans", "zh-hant"]:
                processors.append("mwt")
            processors.append("pos")
            processors.append("constituency")

            processors_list = ",".join(processors)

            # Build package dictionary to specify which processor uses which package
            package_config = {"constituency": model_package}
            # For non-English/German, we try to use the same package for POS
            # if it's a combined model
            if lang not in ["en", "de"]:
                package_config["pos"] = model_package
            # For English/German, POS will default to 'combined' or 'default' implicitly

            # Initialize pipeline
            cls._pipelines[cache_key] = stanza.Pipeline(
                lang=lang,
                processors=processors_list,
                package=package_config,  # type: ignore
                model_dir=STANZA_DIR,
                use_gpu=use_gpu,
            )

        nlp = cls._pipelines[cache_key]
        doc: Any = nlp(text)

        if not doc.sentences:
            return None

        if len(doc.sentences) == 1:
            constituency_string = str(doc.sentences[0].constituency)
            root = LispParser.to_anytree(constituency_string)
            if root:
                root.raw_lisp = constituency_string
            return root

        # Multi-sentence: Wrap in a super-root
        root = SyntaxNode("ROOT")
        for sent in doc.sentences:
            child = LispParser.to_anytree(str(sent.constituency))
            if child:
                child.parent = root

        return root
