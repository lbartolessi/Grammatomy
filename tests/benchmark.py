import logging
import time

import spacy

from grammatomy import get_syntax_tree
from grammatomy.engines.spacy_engine import SpacyEngine
from grammatomy.engines.stanza_engine import StanzaEngine

# Disable verbose logging during benchmark
logging.getLogger("grammatomy").setLevel(logging.ERROR)

STANZA_CHARLM_DESC = "Stanza (CharLM)"

# Test Data: Complex sentences to stress the parsers
SENTENCES = {
    "es": (
        "Mientras el comité que el rector, que había asumido el cargo después de que la crisis "
        "institucional que se desencadenó cuando se hicieron públicos los informes cuya redacción "
        "se había encargado a consultores externos a los que nadie en la facultad recordaba haber "
        "visto, constituyó con la intención declarada de evaluar las propuestas que los "
        "departamentos que, a su vez, dependían de unidades administrativas cuya existencia "
        "muchos profesores desconocían hasta entonces habían remitido, deliberaba sobre la "
        "conveniencia de aceptar un plan que, aunque prometía simplificar los procedimientos "
        "mediante los cuales se asignaban los recursos que permitían sostener los proyectos que "
        "daban sentido a la investigación que justificaba la universidad ante la sociedad, "
        "introducía criterios cuya aplicación, según advertían quienes habían participado en "
        "reformas anteriores que terminaron produciendo efectos distintos de los que se habían "
        "anunciado, alteraría de forma irreversible la relación entre docencia, investigación y "
        "gestión, algunos miembros, conscientes de que la decisión que se adoptara sería "
        "interpretada como un precedente del que dependerían futuras modificaciones que nadie se "
        "atrevería a revertir, optaron por aplazar una votación que, aun cuando parecía puramente "
        "técnica, revelaba tensiones latentes que el discurso oficial, cuidadosamente elaborado "
        "para evitar referencias explícitas a los conflictos que "
        "atravesaban la institución, llevaba años intentando disimular."
    ),
    "en": "The scientist confirmed that the results, which were obtained after the experiment "
    "that the team conducted last year, significantly contradict the previous theories.",
    "fr": "Longtemps, je me suis couché de bonne heure. Parfois, à peine ma bougie éteinte, "
    "mes yeux se fermaient si vite que je n'avais pas le temps de me dire: « Je m'endors. »",
    "it": "Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura, ché la diritta via era smarrita.",
    "pt": "As armas e os barões assinalados, que da ocidental praia lusitana, por mares nunca de antes navegados, passaram ainda além da Taprobana.",
}

# Configuration Matrix based on Inventory Findings
CONFIGS = [
    # Spanish: Stanza is the only viable option (PlanTL failed, Benepar is fallback)
    {
        "engine": "stanza",
        "lang": "es",
        "model_package": "combined_bertin-roberta",
        "desc": "Stanza (Transformer)",
    },
    {
        "engine": "stanza",
        "lang": "es",
        "model_package": "combined_charlm",
        "desc": STANZA_CHARLM_DESC,
    },
    # English: Comparison ground
    {
        "engine": "stanza",
        "lang": "en",
        "model_package": "ptb3-revised_electra-large",
        "desc": "Stanza (Electra)",
    },
    {
        "engine": "spacy",
        "lang": "en",
        "model_package": "benepar_en3",
        "desc": "Benepar (Official)",
    },
    # French: Benepar is critical (Stanza lacks constituency)
    {
        "engine": "spacy",
        "lang": "fr",
        "model_package": "benepar_fr2",
        "desc": "Benepar (Official)",
    },
    # Italian: Stanza strong suit (Using CharLM to fit in VRAM)
    {
        "engine": "stanza",
        "lang": "it",
        "model_package": "vit_charlm",
        "desc": STANZA_CHARLM_DESC,
    },
    # Portuguese: Stanza strong suit (Using CharLM to fit in VRAM)
    {
        "engine": "stanza",
        "lang": "pt",
        "model_package": "cintil_charlm",
        "desc": STANZA_CHARLM_DESC,
    },
    # German: Switched to Stanza due to Benepar incompatibility
    {
        "engine": "stanza",
        "lang": "de",
        "model_package": "spmrl_charlm",
        "desc": STANZA_CHARLM_DESC,
    },
]

SPACY_BASE_MODELS = {
    "en": "en_core_web_lg",
    "fr": "fr_core_news_lg",
}


def ensure_spacy_model(lang):
    """Downloads the required spaCy base model if not already installed."""
    model_name = SPACY_BASE_MODELS.get(lang)
    if model_name:
        try:
            spacy.load(model_name)
        except OSError:
            print(f" spaCy model '{model_name}' not found. Downloading...")
            spacy.cli.download(model_name)  # type: ignore


def run_benchmark():
    print(f"\n{'='*95}")
    print(
        f"{'Language':<5} | {'Engine / Model':<35} | {'Cold Start (s)':<15} | "
        f"{'Warm Start (s)':<15} | {'Status':<8}"
    )
    print(f"{'-'*95}")

    for cfg in CONFIGS:
        lang = cfg["lang"]
        desc = cfg["desc"]
        text = SENTENCES.get(lang, SENTENCES["en"])

        # Prepare params
        params = {
            "engine": cfg["engine"],
            "lang": lang,
            "model_package": cfg["model_package"],
            "use_gpu": True,  # Try GPU if available
        }

        try:
            # Clear memory before each run to avoid OOM on 4GB VRAM
            StanzaEngine.clear_cache()
            SpacyEngine.clear_cache()

            # Ensure dependencies for Benepar are met
            if cfg["engine"] == "spacy":
                ensure_spacy_model(lang)

            # 1. Cold Start: Includes model loading/downloading
            start_time = time.time()
            # Note: StanzaEngine caches pipelines, so we rely on the script being a fresh process
            # or the key being unique.
            root = get_syntax_tree(text, params=params)
            cold_time = time.time() - start_time

            if not root:
                raise ValueError("No tree returned")

            # 2. Warm Start: Inference only (pipeline cached)
            start_time = time.time()
            root = get_syntax_tree(text, params=params)
            warm_time = time.time() - start_time

            status = "✅ OK"

        except Exception as e:  # pylint: disable=broad-exception-caught
            cold_time = 0.0
            warm_time = 0.0
            status = "❌ FAIL"
            print(f"   >>> Debug Error: {e}")

            print(
                f"{lang.upper():<5} | {desc:<35} | {cold_time:<15.4f} | "
                f"{warm_time:<15.4f} | {status:<8}"
            )

    print(f"{'='*95}\n")


if __name__ == "__main__":
    run_benchmark()
