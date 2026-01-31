import stanza
import benepar
import spacy
import nltk
import logging
import subprocess
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelManager")

# --- OFFICIAL INVENTORY ---
# Validated via tests/benchmark.py on 4GB VRAM hardware.

STANZA_MODELS = {
    "es": ["combined_bertin-roberta", "combined_charlm"],
    "it": ["vit_charlm"], # CharLM fits in 4GB VRAM
    "pt": ["cintil_charlm"], # CharLM fits in 4GB VRAM
    "en": ["ptb3-revised_electra-large"],
    "de": ["spmrl_charlm"] # German via Stanza
}

SPACY_MODELS = [
    "en_core_web_lg",
    "fr_core_news_lg",
    "es_core_news_lg"
]

BENEPAR_MODELS = [
    "benepar_en3",
    "benepar_fr2"
]

# --- PATH CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

def download_stanza():
    logger.info("--- Downloading Stanza Models ---")
    stanza_dir = os.path.join(MODELS_DIR, "stanza")
    os.makedirs(stanza_dir, exist_ok=True)
    
    for lang, packages in STANZA_MODELS.items():
        # Always ensure tokenizer is present
        logger.info(f"Checking Stanza base for '{lang}'...")
        # English and Chinese typically don't use MWT
        processors = "tokenize" if lang in ["en", "zh"] else "tokenize,mwt"
        stanza.download(lang, processors=processors, model_dir=stanza_dir)
        
        for pkg in packages:
            logger.info(f"Downloading Stanza package '{pkg}' for '{lang}'...")
            # For English and German, constituency models are often standalone (require default POS)
            if lang in ["en", "de"]:
                stanza.download(lang, processors="pos", model_dir=stanza_dir) # Default POS
                stanza.download(lang, processors="constituency", package=pkg, model_dir=stanza_dir)
            else:
                stanza.download(lang, processors="pos,constituency", package=pkg, model_dir=stanza_dir)

def download_spacy():
    logger.info("\n--- Downloading/Backing up spaCy Models ---")
    spacy_dist_dir = os.path.join(MODELS_DIR, "spacy_dist")
    os.makedirs(spacy_dist_dir, exist_ok=True)
    
    # Version assumption based on current spaCy version (3.7+)
    # We backup the wheels to ensure we have the artifacts locally
    spacy_version = "3.8.0" 
    
    for model in SPACY_MODELS:
        # 1. Ensure installed in environment
        if not spacy.util.is_package(model):
            logger.info(f"Installing spaCy model: {model}")
            spacy.cli.download(model)
        else:
            logger.info(f"spaCy model '{model}' already installed.")
            
        # 2. Backup wheel file (Sovereignty)
        url = f"https://github.com/explosion/spacy-models/releases/download/{model}-{spacy_version}/{model}-{spacy_version}-py3-none-any.whl"
        logger.info(f"Backing up {model} wheel to {spacy_dist_dir}...")
        subprocess.run(["pip", "download", url, "-d", spacy_dist_dir, "--no-deps"], check=False)

def download_benepar():
    logger.info("\n--- Downloading Benepar Models ---")
    benepar_dir = os.path.join(MODELS_DIR, "benepar")
    os.makedirs(benepar_dir, exist_ok=True)
    
    # Ensure NLTK data path includes local directory if needed
    nltk.data.path.append(benepar_dir)
    
    for model in BENEPAR_MODELS:
        try:
            nltk.data.find(f"models/{model}")
            logger.info(f"Benepar model '{model}' found.")
        except LookupError:
            logger.info(f"Downloading Benepar model: {model} to {benepar_dir}")
            benepar.download(model, download_dir=benepar_dir)

def main():
    print("🌳 Grammatomy Model Manager")
    print(f"Target Directory: {MODELS_DIR}")
    print("=====================================================================")
    
    try:
        download_spacy()
        download_benepar()
        download_stanza()
        print("\n✅ All models successfully synchronized.")
    except Exception as e:
        print(f"\n❌ Error during model synchronization: {e}")
        exit(1)

if __name__ == "__main__":
    main()