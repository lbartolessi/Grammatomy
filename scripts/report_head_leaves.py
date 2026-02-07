from pathlib import Path

from core.validation_engine import ValidationEngine

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def report_declared_heads():
    """
    Reports the declared 'head_leaves' for each group in the grammar,
    which are used for the Head-based Lax Validation.
    """
    print("=" * 80)
    print("Reporting Declared Head Leaves for Lax Validation")
    print("-" * 80)
    rules_path = PROJECT_ROOT / "src" / "core" / "rules_es.yaml"
    try:
        engine = ValidationEngine(rules_path=str(rules_path), strategy="lax")
    except FileNotFoundError:
        print(f"ERROR: Rules file not found at '{rules_path}'")
        return
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"ERROR: Failed to initialize ValidationEngine: {e}")
        return

    # --- Print Results Table ---
    print(f"{'AnCora Group':<25} | {'Declared Essential Head (for Lax Validation)':<50}")
    print(f"{'-'*25}-|--{'-'*50}")
    for node_label, config in sorted(engine.rules.items()):
        if config.get("type", "group") == "group":
            head_leaves = config.get("head_leaves", [])
            head_str = ", ".join(head_leaves) if head_leaves else "(none defined)"
            print(f"{node_label:<25} | {head_str}")

    print("=" * 80)


if __name__ == "__main__":
    report_declared_heads()
