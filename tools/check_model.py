#!/usr/bin/env python3
"""
Utility script to verify availability of SOTA models identified in the report.
"""
import logging

from huggingface_hub import model_info
from huggingface_hub.errors import RepositoryNotFoundError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelChecker")

MODELS_TO_CHECK = [
    # Spanish models for Benepar are currently not indexed in NLTK/HF
    ("benepar_en3", "English (Baseline)")
]


def check_huggingface(model_name):
    try:
        # Check if model exists on HF Hub
        info = model_info(model_name)
        print(f"✅ SUCCESS: Found on Hugging Face! Repo ID: '{info.id}'")
        print(f"   -> Downloads: {info.downloads}, Likes: {info.likes}")
    except RepositoryNotFoundError:
        print("❌ FAILED: Not found on Hugging Face either.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"⚠️ HF Check Error: {e}")


def check_stanza_availability():
    # Stanza usually works, but good to verify 'default_accurate'
    import stanza  # pylint: disable=import-outside-toplevel

    print("\n=== Checking Stanza Models ===")
    try:
        stanza.download("es", package="default_accurate", processors="constituency")
        print("✅ SUCCESS: Stanza 'es' (default_accurate) downloaded.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ FAILED: Stanza download error: {e}")


if __name__ == "__main__":
    check_stanza_availability()
