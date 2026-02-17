"""
Project Engine.

Orchestrates the creation and management of Grammatomy projects.
Handles text segmentation, batch parsing, and fragmentation logic
to offload complexity from the frontend.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# We use Stanza for robust sentence segmentation if available,
# otherwise fallback to simple splitting.
try:
    import stanza
except ImportError:
    stanza = None

from core.grammatomy.engines.stanza_engine import StanzaEngine
from core.grammatomy.fragmentation import FragmentationEngine
from core.grammatomy.logger import setup_logging

logger = setup_logging(__name__)


class ProjectEngine:
    """
    Central logic for Project operations.
    """

    def __init__(self):
        self.fragmentation_engine = FragmentationEngine()

    def create_project(
        self, text: str, name: str = "New Project", lang: str = "es"
    ) -> Dict[str, Any]:
        """
        Creates a full project structure from raw text.
        1. Segments text into sentences.
        2. Parses each sentence into PTB.
        3. Fragments complex trees.
        4. Returns the Project JSON structure.
        """
        logger.info("Creating project '%s' (lang=%s, len=%d)", name, lang, len(text))

        # 1. Segmentation
        sentences = self._segment_text(text, lang)
        logger.info("Segmented into %d sentences.", len(sentences))

        units = []
        for i, sent_text in enumerate(sentences):
            unit_id = f"u{i + 1}"
            try:
                # 2. Parsing
                # We use StanzaEngine directly. In the future, this could be configurable.
                # Note: StanzaEngine.get_tree returns a SyntaxNode. We need the PTB string.
                # Ideally, StanzaEngine should expose a method to get PTB string directly or we export the node.
                # For now, let's assume we use the existing get_syntax_tree wrapper or engine directly.
                # To keep it clean, let's use StanzaEngine.
                root = StanzaEngine.get_tree(sent_text, lang=lang)
                if not root:
                    logger.warning("Failed to parse sentence %d: '%s'", i, sent_text[:30])
                    continue

                # We need the PTB string. StanzaEngine attaches raw_lisp to the root if available,
                # or we can export it.
                from core.grammatomy.exporters.ptb_exporter import PtbExporter

                exporter = PtbExporter()
                full_ptb = exporter.export(root)

                # 3. Fragmentation
                main_ptb, subtrees, integrity = self.fragmentation_engine.fragment(full_ptb)

                # 4. Build Unit
                unit = {
                    "id": unit_id,
                    "sentence": sent_text,
                    "original_ptb": full_ptb,
                    "current_ptb": main_ptb,
                    "subtrees": subtrees,
                    "status": "draft",
                    "metadata": {"integrity_check": integrity} if integrity else {},
                }
                units.append(unit)

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error processing unit %s: %s", unit_id, e)
                # Add a placeholder unit so the user can fix it manually?
                # Or just skip? Let's skip for now to avoid corrupt state.

        project = {
            "meta": {
                "version": "1.0",
                "name": name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            "source_text": text,
            "units": units,
        }

        return project

    def _segment_text(self, text: str, lang: str) -> List[str]:
        """
        Segments text into sentences using Stanza's tokenizer.
        """
        # Use Stanza's pipeline just for tokenization if possible, or reuse the engine's pipeline
        # StanzaEngine caches pipelines. Let's try to use that.
        try:
            nlp = StanzaEngine._get_pipeline(
                lang, "default", False
            )  # pylint: disable=protected-access
            doc = nlp(text)
            return [sentence.text for sentence in doc.sentences]
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Stanza segmentation failed (%s). Fallback to simple split.", e)
            # Fallback: Split by newlines or simple punctuation
            return [s.strip() for s in text.split("\n") if s.strip()]
