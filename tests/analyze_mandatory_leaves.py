import sys
from pathlib import Path

# Add project root to path to allow importing from src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.validation_engine import ValidationEngine


def analyze_grammar_intersections():
    """
    Analyzes the grammar rules to test the hypothesis of deducing
    mandatory POS tags via intersection of all possible expansions.
    """
    print("=" * 80)
    print("Running Algorithmic Mandatory POS Analysis")
    print(
        "Hypothesis: Essential POS tags can be deduced by intersecting all possible expansions."
    )
    print("-" * 80)

    try:
        rules_path = PROJECT_ROOT / "src" / "core" / "rules_es.yaml"
        engine = ValidationEngine(rules_path=str(rules_path), strategy="lax")
    except FileNotFoundError:
        print(f"ERROR: Rules file not found at '{rules_path}'")
        return
    except Exception as e:
        print(f"ERROR: Failed to initialize ValidationEngine: {e}")
        return

    results = []
    # We iterate through the rules in the order they appear in the file for consistency
    for node_label, config in engine.rules.items():
        if config.get("type") == "group":
            # The cache is pre-populated on engine initialization
            mandatory_leaves = engine._mandatory_leaves_cache.get(node_label, set())
            results.append((node_label, mandatory_leaves))

    # --- Print Results Table ---
    print(f"{'AnCora Group':<25} | {'Deduced Mandatory POS (by Intersection)':<50}")
    print(f"{'-'*25}-|--{'-'*50}")

    for group, pos_set in results:
        pos_str = ", ".join(sorted(list(pos_set))) if pos_set else "(empty set)"
        print(f"{group:<25} | {pos_str}")

    print("=" * 80)


if __name__ == "__main__":
    analyze_grammar_intersections()
