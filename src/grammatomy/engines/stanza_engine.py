from typing import Optional, Dict, Any
import stanza
import gc
import os
import torch
from pathlib import Path
from anytree import Node
from ..parsers.lisp_parser import LispParser

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
        cls._pipelines.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @classmethod
    def get_tree(
        cls, text: str, lang: str = "es", model_package: str = "default", use_gpu: bool = True
    ) -> Optional[Node]:
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
            
            # Download base processors (tokenize, mwt)
            stanza.download(lang, processors="tokenize,mwt" if "mwt" in processors else "tokenize", model_dir=STANZA_DIR)
            
            # 2. Download the specific package for pos/constituency
            # Note: For English and German, constituency models often don't bundle POS, so we rely on default for POS
            if lang in ["en", "de"]:
                 # Ensure default POS is available
                 stanza.download(lang, processors="pos", model_dir=STANZA_DIR)
                 stanza.download(lang, processors="constituency", package=model_package, model_dir=STANZA_DIR)
            else:
                 # For ES, IT, PT, use the combined model for both
                 stanza.download(lang, processors="pos,constituency", package=model_package, model_dir=STANZA_DIR)

            # Build package dictionary to specify which processor uses which package
            package_config = {
                "constituency": model_package
            }
            # For non-English/German, we try to use the same package for POS if it's a combined model
            if lang not in ["en", "de"]:
                package_config["pos"] = model_package
            # For English/German, POS will default to 'combined' or 'default' implicitly

            # Initialize pipeline
            cls._pipelines[cache_key] = stanza.Pipeline(
                lang=lang,
                processors=processors_list,
                package=package_config,
                model_dir=STANZA_DIR,
                use_gpu=use_gpu,
            )

        nlp = cls._pipelines[cache_key]
        doc: Any = nlp(text)

        if not doc.sentences:
            return None

        # We take the first sentence's tree.
        # TODO: Handle multi-sentence input (wrap in a super-root?)
        constituency_string = str(doc.sentences[0].constituency)

        root = LispParser.to_anytree(constituency_string)
        if root:
            root.raw_lisp = constituency_string  # Attach raw source for debugging/demo
            
        return root
