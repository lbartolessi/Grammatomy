#!/usr/bin/env python3
"""
Utility script to verify availability of SOTA models identified in the report.
"""
import benepar
import spacy
import logging
import nltk
from huggingface_hub import model_info
from huggingface_hub.utils import RepositoryNotFoundError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelChecker")

MODELS_TO_CHECK = [
    # Spanish models for Benepar are currently not indexed in NLTK/HF
    ("benepar_en3", "English (Baseline)")
]

def check_benepar_availability():
    print("=== Checking Benepar Models ===")
    for model_name, description in MODELS_TO_CHECK:
        print(f"\nChecking: {model_name} ({description})...")
        try:
            # Try standard download
            benepar.download(model_name)
            
            # Rigorous check: try to find it in NLTK data
            nltk.data.find(f"models/{model_name}")
            print(f"✅ SUCCESS: {model_name} is installed and available.")
        except LookupError:
            print(f"⚠️  NLTK: {model_name} not in index. Checking Hugging Face...")
            check_huggingface(model_name)
        except Exception as e:
            print(f"⚠️ ERROR: Download crashed with {type(e).__name__}: {e}")

def check_huggingface(model_name):
    try:
        # Check if model exists on HF Hub
        info = model_info(model_name)
        print(f"✅ SUCCESS: Found on Hugging Face! Repo ID: '{info.modelId}'")
        print(f"   -> Downloads: {info.downloads}, Likes: {info.likes}")
    except RepositoryNotFoundError:
        print(f"❌ FAILED: Not found on Hugging Face either.")
    except Exception as e:
        print(f"⚠️ HF Check Error: {e}")

def check_stanza_availability():
    # Stanza usually works, but good to verify 'default_accurate'
    import stanza
    print("\n=== Checking Stanza Models ===")
    try:
        stanza.download("es", package="default_accurate", processors="constituency")
        print("✅ SUCCESS: Stanza 'es' (default_accurate) downloaded.")
    except Exception as e:
        print(f"❌ FAILED: Stanza download error: {e}")

if __name__ == "__main__":
    check_benepar_availability()
    check_stanza_availability()