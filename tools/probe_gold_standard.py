import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))  # To import resources

from resources.gold_sentences import GOLD_SENTENCES

from core.grammatomy import get_syntax_tree
from core.grammatomy.visualization.ascii_renderer import render_ascii_colored


def probe_model(engine="stanza", lang="es"):
    """
    Runs the Gold Standard sentences through the specified engine
    and prints a report comparing expected vs actual structure.
    """
    print(f"\n{'='*80}")
    print(
        f"🔍 GRAMMATOMY GOLD STANDARD PROBE | Engine: {engine.upper()} | Lang: {lang.upper()}"
    )
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
            print(f"\n🔹 Case ID: {case['id']}")
            print(f"   📝 Text:      \"{case['text']}\"")
            print(f"   👀 Phenomenon: {case['phenomenon']}")
            print(f"   🎯 Expected:   {case['expected']}")

            try:
                # 1. Parse
                root = get_syntax_tree(case["text"], params=params)

                if not root:
                    print("   ❌ ERROR: Parser returned no tree.")
                    continue

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

                print(f"   🤖 Model Output:")
                # Indent the tree
                for line in clean_tree.split("\n"):
                    print(f"      {line}")

                # 3. Quick Analysis (Heuristics)
                # Check for empty subjects (AnCora style) vs Missing subjects (Stanza style)
                has_elliptic = "elliptic" in str(root) or "sn" in [
                    c.name for c in root.children if not c.children
                ]

                print(f"   🕵️  Analysis:")
                if "Sujeto Elíptico" in category:
                    if has_elliptic:
                        print(
                            "      -> Model generated an empty/elliptic node (AnCora compliant)."
                        )
                    else:
                        print(
                            "      -> Model omitted the subject (Standard Neural behavior)."
                        )

                if "Impersonalidad" in category:
                    # Check if there is a subject
                    # This is a naive check, real logic is in ValidationEngine
                    pass

            except Exception as e:
                print(f"   ❌ EXCEPTION: {e}")

    print(f"\n{'='*80}")
    print("End of Probe.")


if __name__ == "__main__":
    # Default to Spanish Stanza, as AnCora is Spanish/Catalan
    probe_model(engine="stanza", lang="es")
