import importlib.util
import logging
from pathlib import Path

import pytest

from core.grammatomy import get_syntax_tree

logger = logging.getLogger(__name__)

# Dynamic import for local resource
# Assuming tests are run from project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCE_PATH = PROJECT_ROOT / "resources" / "gold_sentences.py"


def load_gold_sentences():
    if not RESOURCE_PATH.exists():
        # Return empty dict if resource missing, test will skip or fail gracefully
        return {}

    spec = importlib.util.spec_from_file_location("gold_sentences", RESOURCE_PATH)
    if spec and spec.loader:
        gs_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gs_module)
        return gs_module.GOLD_SENTENCES
    return {}


GOLD_SENTENCES = load_gold_sentences()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not GOLD_SENTENCES, reason="Gold sentences resource not found")
@pytest.mark.parametrize("category", GOLD_SENTENCES.keys())
def test_gold_standard_sentences(category):
    """
    Probes the Gold Standard sentences.
    Currently checks for successful parsing and logs the output.
    """
    sentences = GOLD_SENTENCES[category]
    params = {
        "engine": "stanza",
        "lang": "es",
        "model_package": "default",
        "use_gpu": False,
    }

    for case in sentences:
        logger.info(f"Testing Case ID: {case['id']} - {case['phenomenon']}")

        try:
            root = get_syntax_tree(case["text"], params=params)
            assert root is not None, f"Parser returned no tree for case {case['id']}"

            # Here we could add assertions for specific expected structures
            # For now, we ensure it parses without error

        except Exception as e:  # pylint: disable=broad-exception-caught
            pytest.fail(f"Exception in Gold Standard Case {case['id']}: {e}")
