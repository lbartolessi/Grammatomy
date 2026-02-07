import logging
import time

import spacy

from core.grammatomy import config, get_syntax_tree
from core.grammatomy.engines.spacy_engine import SpacyEngine
from core.grammatomy.engines.stanza_engine import StanzaEngine

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
        "anunciado, alteraría de forma irreversible la relación entre docencia, "
        "investigación y gestión, algunos miembros, conscientes de que la decisión que se "
        "adoptara sería interpretada como un precedente del que dependerían futuras "
        "modificaciones que nadie se atrevería a revertir, optaron por aplazar una "
        "votación que, aun cuando parecía puramente "
        "técnica, revelaba tensiones latentes que el discurso oficial, cuidadosamente "
        "elaborado para evitar referencias explícitas a los conflictos que "
        "atravesaban la institución, llevaba años intentando disimular."
    ),
    "en": "The scientist confirmed that the results, which were obtained after the experiment "
    "that the team conducted last year, significantly contradict the previous theories.",
    "fr": "Longtemps, je me suis couché de bonne heure. Parfois, à peine ma bougie éteinte, "
    "mes yeux se fermaient si vite que je n'avais pas le temps de me dire: « Je m'endors. »",
    "it": "Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura, ché la diritta via era smarrita.",
    "pt": "As armas e os barões assinalados, que da ocidental praia lusitana, por mares nunca de antes navegados, passaram ainda além da Taprobana.",
}

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


def _measure_performance(
    engine_name: str, lang: str, model_package: str, text: str
) -> tuple[float, float, str]:
    """Runs a single benchmark case and returns (cold_time, warm_time, status)."""
    params = {
        "engine": engine_name,
        "lang": lang,
        "model_package": model_package,
        "use_gpu": True,
    }

    try:
        # Clear memory before each run
        StanzaEngine.clear_cache()
        SpacyEngine.clear_cache()

        if engine_name == "spacy":
            ensure_spacy_model(lang)

        # 1. Cold Start
        start_time = time.time()
        root = get_syntax_tree(text, params=params)
        cold_time = time.time() - start_time

        if not root:
            raise ValueError("No tree returned")

        # 2. Warm Start
        start_time = time.time()
        get_syntax_tree(text, params=params)
        warm_time = time.time() - start_time

        return cold_time, warm_time, "✅ OK"

    except Exception:  # pylint: disable=broad-exception-caught
        return 0.0, 0.0, "❌ FAIL"


def run_benchmark():
    print(f"\n{'='*95}")
    print(
        f"{'Language':<5} | {'Engine / Model':<35} | {'Cold Start (s)':<15} | "
        f"{'Warm Start (s)':<15} | {'Status':<8}"
    )
    print(f"{'-'*95}")

    # Iterate dynamically over configured engines
    # This respects Model Sovereignty defined in config.yaml
    engines_conf = config._data.get("engines", {})  # pylint: disable=protected-access

    for engine_name, engine_data in engines_conf.items():
        if not engine_data.get("enabled", False):
            continue

        for lang, models in engine_data.get("languages", {}).items():
            for model_package in models:
                desc = f"{engine_name.capitalize()} ({model_package})"
                text = SENTENCES.get(lang, SENTENCES["en"])

                cold_time, warm_time, status = _measure_performance(
                    engine_name, lang, model_package, text
                )

                print(
                    f"{lang.upper():<5} | {desc:<35} | {cold_time:<15.4f} | "
                    f"{warm_time:<15.4f} | {status:<8}"
                )

    print(f"{'='*95}\n")


if __name__ == "__main__":
    run_benchmark()
