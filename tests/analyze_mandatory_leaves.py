from pathlib import Path

from core.grammatomy.validation_engine import ValidationEngine

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def analyze_grammar_intersections():
    """
    Analyzes the grammar rules to test the hypothesis of deducing
    mandatory POS tags via intersection of all possible expansions.
    """
    print("=" * 80)
    print("Running Algorithmic Mandatory POS Analysis")
    print("Hypothesis: Essential POS tags can be deduced by intersecting all possible expansions.")
    print("-" * 80)

    rules_path = PROJECT_ROOT / "src" / "core" / "rules_es.yaml"
    try:
        engine = ValidationEngine(rules_path=str(rules_path), lang="es")
    except FileNotFoundError:
        print(f"ERROR: Rules file not found at '{rules_path}'")
        return
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"ERROR: Failed to initialize ValidationEngine: {e}")
        return

    results = []
    # We iterate through the rules in the order they appear in the file for consistency
    for node_label, config in engine.rules.items():
        if config.get("type") == "group":
            # The cache is pre-populated on engine initialization
            mandatory = engine.mandatory_children.get(node_label, set())
            results.append((node_label, mandatory))

    # --- Print Results Table ---
    print(f"{'AnCora Group':<25} | {'Mandatory Children (Immediate)':<50}")
    print(f"{'-'*25}-|--{'-'*50}")

    for group, pos_set in results:
        pos_str = ", ".join(sorted(pos_set)) if pos_set else "(empty set)"
        print(f"{group:<25} | {pos_str}")

    print("=" * 80)


if __name__ == "__main__":
    analyze_grammar_intersections()
