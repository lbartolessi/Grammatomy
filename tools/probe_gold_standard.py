import importlib.util
from pathlib import Path

from core.grammatomy import get_syntax_tree
from core.grammatomy.visualization.ascii_renderer import render_ascii_colored

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_PATH = PROJECT_ROOT / "resources" / "gold_sentences.py"

# Dynamic import for local resource without sys.path manipulation
spec = importlib.util.spec_from_file_location("gold_sentences", RESOURCE_PATH)
if spec and spec.loader:
    gs_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gs_module)
    GOLD_SENTENCES = gs_module.GOLD_SENTENCES
else:
    raise ImportError(f"Could not load gold_sentences from {RESOURCE_PATH}")


def _probe_case(case, params, category):
    """Process a single test case."""
    print(f"\n🔹 Case ID: {case['id']}")
    print(f"   📝 Text:      \"{case['text']}\"")
    print(f"   👀 Phenomenon: {case['phenomenon']}")
    print(f"   🎯 Expected:   {case['expected']}")

    try:
        # 1. Parse
        root = get_syntax_tree(case["text"], params=params)

        if not root:
            print("   ❌ ERROR: Parser returned no tree.")
            return

        # 2. Render (Strip HTML tags for console readability)
        ascii_tree = render_ascii_colored(root)
        # Simple strip of span tags for console output
        clean_tree = (
            ascii_tree.replace("<span class='tree-connector'>", "")
            .replace("</span>", "")
            .replace("<span class='style-phrasal'>", "")
            .replace("<span class='style-pos'>", "")
            .replace("<span class='style-word'>", "")
            .replace("<span class='style-punct'>", "")
        )

        print("   🤖 Model Output:")
        # Indent the tree
        for line in clean_tree.split("\n"):
            print(f"      {line}")

        # 3. Quick Analysis (Heuristics)
        # Check for empty subjects (AnCora style) vs Missing subjects (Stanza style)
        has_elliptic = "elliptic" in str(root) or "sn" in [
            c.name for c in root.children if not c.children
        ]

        print("   🕵️  Analysis:")
        if "Sujeto Elíptico" in category:
            if has_elliptic:
                print("      -> Model generated an empty/elliptic node (AnCora compliant).")
            else:
                print("      -> Model omitted the subject (Standard Neural behavior).")

        if "Impersonalidad" in category:
            # Check if there is a subject
            # This is a naive check, real logic is in ValidationEngine
            pass

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ❌ EXCEPTION: {e}")


def probe_model(engine="stanza", lang="es"):
    """
    Runs the Gold Standard sentences through the specified engine
    and prints a report comparing expected vs actual structure.
    """
    print(f"\n{'='*80}")
    print(f"🔍 GRAMMATOMY GOLD STANDARD PROBE | Engine: {engine.upper()} | Lang: {lang.upper()}")
    print(f"{'='*80}\n")

    params = {
        "engine": engine,
        "lang": lang,
        "model_package": "default",
        "use_gpu": False,
    }

    for category, sentences in GOLD_SENTENCES.items():
        print(f"\n📂 CATEGORY: {category}")
        print(f"{'-'*80}")

        for case in sentences:
            _probe_case(case, params, category)

    print(f"\n{'='*80}")
    print("End of Probe.")


if __name__ == "__main__":
    # Default to Spanish Stanza, as AnCora is Spanish/Catalan
    probe_model(engine="stanza", lang="es")
