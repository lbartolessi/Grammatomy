import gc
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import benepar
import nltk
import spacy
import torch
from huggingface_hub import snapshot_download

from ..parsers.lisp_parser import LispParser, SyntaxNode

logger = logging.getLogger(__name__)

# Register local models path for NLTK/Benepar
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BENEPAR_DIR = str(PROJECT_ROOT / "models" / "benepar")
nltk.data.path.append(BENEPAR_DIR)


def _patch_transformers():
    """
    Monkey-patch for 'transformers' library to fix Benepar compatibility issues.
    Restores 'build_inputs_with_special_tokens' for T5 and XLM-R tokenizers.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from transformers import T5TokenizerFast  # type: ignore
        from transformers import XLMRobertaTokenizerFast  # type: ignore
        from transformers import T5Tokenizer, XLMRobertaTokenizer

        # Patch for T5 (English benepar_en3)
        def t5_build_inputs(self, token_ids_0, token_ids_1=None):
            if token_ids_1 is None:
                return token_ids_0 + [self.eos_token_id]
            return token_ids_0 + [self.eos_token_id] + token_ids_1 + [self.eos_token_id]

        for cls in [T5Tokenizer, T5TokenizerFast]:
            if not hasattr(cls, "build_inputs_with_special_tokens"):
                cls.build_inputs_with_special_tokens = t5_build_inputs

        # Patch for XLM-RoBERTa (French benepar_fr2, Spanish benepar_es2)
        def xlmr_build_inputs(self, token_ids_0, token_ids_1=None):
            bos = [self.bos_token_id]
            eos = [self.eos_token_id]
            if token_ids_1 is None:
                return bos + token_ids_0 + eos
            return bos + token_ids_0 + eos + eos + token_ids_1 + eos

        for cls in [XLMRobertaTokenizer, XLMRobertaTokenizerFast]:
            if not hasattr(cls, "build_inputs_with_special_tokens"):
                cls.build_inputs_with_special_tokens = xlmr_build_inputs

    except ImportError:
        logger.warning("Could not patch transformers. Benepar might fail.")


class SpacyEngine:
    """
    Adapter for spaCy + Benepar.
    Leverages Hugging Face models for multilingual constituency parsing.
    """

    _pipelines: Dict[str, spacy.language.Language] = {}

    # Default recommended models per language
    MODEL_MAP = {
        "es": "benepar_en3",  # Fallback: 'benepar_es2' not available in NLTK index yet
        "en": "benepar_en3",
        "fr": "benepar_fr2",
        "de": "benepar_de2",
    }

    @classmethod
    def clear_cache(cls):
        """Clears the pipeline cache and forces garbage collection."""
        cls._pipelines.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Apply patch on module load to ensure Benepar finds the methods
    _patch_transformers()

    @classmethod
    def _resolve_model(cls, lang: str, model_package: str) -> str:
        """Resolves the model name and ensures it is downloaded."""
        # Determine actual model name
        if model_package == "default":
            hf_model = cls.MODEL_MAP.get(lang, "benepar_en3")
        else:
            hf_model = model_package

        # Resolve model path/download
        # If it looks like a HF repo (has /) and is not a local path
        if "/" in hf_model and not os.path.exists(hf_model):
            try:
                logger.info("Downloading '%s' from Hugging Face...", hf_model)
                snapshot_download(repo_id=hf_model)
            except Exception as e:  # pragma: no cover
                logger.error("HF download failed for %s: %s", hf_model, e)
                raise RuntimeError(
                    f"Could not download model '{hf_model}' from Hugging Face."
                ) from e
        elif "/" not in hf_model:
            # Standard Benepar model (e.g., benepar_en3)
            try:
                nltk.data.find(f"models/{hf_model}")
            except LookupError:
                benepar.download(hf_model)

        return hf_model

    @classmethod
    def _create_pipeline(
        cls, lang: str, hf_model: str, use_gpu: bool
    ) -> spacy.language.Language:
        """Creates and configures the spaCy pipeline with Benepar."""
        # 1. Load base spaCy model
        # We try to load a large model for better POS tags, fallback to blank if missing
        try:
            if lang == "es":
                nlp = spacy.load("es_core_news_lg")
            elif lang == "en":
                nlp = spacy.load("en_core_web_lg")
            elif lang == "fr":
                nlp = spacy.load("fr_core_news_lg")
            elif lang == "de":
                nlp = spacy.load("de_core_news_lg")
            else:
                nlp = spacy.blank(lang)
        except OSError:
            # Fallback if specific model is not installed
            logger.warning(
                "Base spaCy model for '%s' not found. Using blank model.", lang
            )
            nlp = spacy.blank(lang)

        # Ensure we have a sentencizer if the model is blank/basic
        if not nlp.has_pipe("sentencizer") and not nlp.has_pipe("parser"):
            nlp.add_pipe("sentencizer")

        # 2. Add Benepar component
        if use_gpu:
            # Hack to prevent some benepar issues on GPU sometimes
            benepar.mkdtemp = lambda: None  # type: ignore
            # Note: Benepar GPU usage is handled by torch global state usually

        nlp.add_pipe("benepar", config={"model": hf_model})
        return nlp

    @classmethod
    def get_tree(
        cls,
        text: str,
        lang: str = "es",
        model_package: str = "default",
        use_gpu: bool = False,
    ) -> Optional[SyntaxNode]:
        """Generates a constituency tree using spaCy and Benepar."""
        hf_model = cls._resolve_model(lang, model_package)
        cache_key = f"{lang}_{hf_model}_{use_gpu}"

        if cache_key not in cls._pipelines:
            cls._pipelines[cache_key] = cls._create_pipeline(lang, hf_model, use_gpu)

        nlp = cls._pipelines[cache_key]
        doc = nlp(text)

        # Extract tree from the first sentence
        sents = list(doc.sents)
        if sents:
            sent = sents[0]
            raw_lisp = sent._.parse_string
            root = LispParser.to_anytree(raw_lisp)
            if root:
                root.raw_lisp = raw_lisp
            return root

        return None
