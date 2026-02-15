import logging

import pytest

from core.grammatomy import get_syntax_tree
from core.grammatomy.grammar import validate_structure

# Configure logging
logger = logging.getLogger(__name__)

# --- STRESS CORPUS ---
CORPUS = [
    {
        "lang": "es",
        "engine": "stanza",
        "desc": "Spanish Complex (Subordination & Coordination)",
        "text": (
            "Mientras el comité deliberaba sobre la conveniencia de aceptar un plan que "
            "prometía simplificar los procedimientos, algunos miembros optaron por aplazar "
            "una votación que revelaba tensiones latentes."
        ),
    },
    {
        "lang": "es",
        "engine": "stanza",
        "desc": "Spanish Mixed (Direct Object & Prepositions)",
        "text": "El veloz murciélago hindú comía feliz cardillo y kiwi en la cueva.",
    },
    {
        "lang": "en",
        "engine": "spacy",  # Uses Benepar
        "desc": "English Standard (PTB)",
        "text": (
            "The scientist confirmed that the results significantly contradict "
            "the previous theories."
        ),
    },
    {
        "lang": "pt",
        "engine": "stanza",
        "desc": "Portuguese (CINTIL / CharLM)",
        "text": (
            "As armas e os barões assinalados, que da ocidental praia lusitana, "
            "por mares nunca de antes navegados, passaram ainda além da Taprobana."
        ),
    },
    {
        "lang": "it",
        "engine": "stanza",
        "desc": "Italian (VIT / CharLM)",
        "text": (
            "Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura, "
            "ché la diritta via era smarrita."
        ),
    },
]


@pytest.mark.integration
@pytest.mark.slow
def test_batch_validation_corpus():
    """
    Runs the stress corpus through the parsers and validates the structure.
    This test ensures that the parsers don't crash and return a valid tree object.
    """

    for item in CORPUS:
        lang = item["lang"]
        engine = item["engine"]
        desc = item["desc"]
        text = item["text"]

        logger.info(f"Testing [{lang.upper()}] {desc} with {engine}")

        try:
            # 1. Parse
            root = get_syntax_tree(text, params={"lang": lang, "engine": engine})

            # Assert tree is generated
            assert root is not None, f"Parsing failed for {desc} ({lang})"

            # 2. Validate
            warnings = validate_structure(root)

            if warnings:
                logger.warning("Warnings for %s: %s", desc, warnings)

        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"Skipping {desc} due to missing optional dependency: {e}")
            continue

        except Exception as e:  # pylint: disable=broad-exception-caught
            pytest.fail(f"Exception during batch validation of {desc}: {e}")
