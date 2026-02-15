import logging

import pytest
import stanza

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.slow
def test_probe_stanza_es():
    """Probe Spanish Stanza parsing."""
    sentences = [
        "El gato rápido come pescado.",
    ]

    try:
        # Ensure model is present (this might download if not present,
        # which is okay for integration tests)
        stanza.download(
            "es",
            processors="tokenize,pos,constituency",
            package="default_accurate",
            verbose=False,
        )

        nlp = stanza.Pipeline(
            "es",
            processors="tokenize,pos,constituency",
            package="default_accurate",
            verbose=False,
            use_gpu=False,  # Force CPU for CI/Test stability
        )

        for text in sentences:
            doc = nlp(text)
            assert len(doc.sentences) > 0  # type: ignore
            tree = doc.sentences[0].constituency  # type: ignore
            assert tree is not None
            logger.info("Stanza ES Tree: %s", tree)

    except Exception as e:  # pylint: disable=broad-exception-caught
        pytest.fail(f"Stanza ES Probe failed: {e}")


@pytest.mark.integration
@pytest.mark.slow
def test_probe_spacy_benepar_en():
    """Probe English Benepar parsing."""
    spacy = pytest.importorskip("spacy")

    try:
        # pylint: disable=import-outside-toplevel, unused-import
        import benepar

        # Check if spacy model is installed, skip if not to avoid CI failure on missing heavy assets
        if not spacy.util.is_package("en_core_web_md"):
            pytest.skip("spacy model 'en_core_web_md' not installed")

        nlp = spacy.load("en_core_web_md")
        if "benepar" not in nlp.pipe_names:
            try:
                nlp.add_pipe("benepar", config={"model": "benepar_en3"})
            except Exception as e:  # pylint: disable=broad-exception-caught
                pytest.skip(f"Benepar model load failed (likely missing model): {e}")

        doc = nlp("The quick cat eats fish.")
        sent = list(doc.sents)[0]

        assert sent._.parse_string is not None
        logger.info("Benepar EN Tree: %s", sent._.parse_string)

    except ImportError:
        pytest.skip("Benepar not installed")
    except Exception as e:  # pylint: disable=broad-exception-caught
        pytest.fail(f"Benepar EN Probe failed: {e}")
