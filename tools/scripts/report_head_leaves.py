import logging
from pathlib import Path

from core.grammatomy.validation_engine import ValidationEngine

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def report_declared_heads():
    """
    Reports the declared 'head_leaves' for each group in the grammar,
    which are used for the Head-based Lax Validation.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Reporting Declared Head Leaves for Lax Validation")
    logger.info("-" * 80)
    rules_path = PROJECT_ROOT / "src" / "core" / "rules_es.yaml"
    try:
        engine = ValidationEngine(rules_path=str(rules_path), lang="es")
    except FileNotFoundError:
        logger.error("ERROR: Rules file not found at '%s'", rules_path)
        return
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("ERROR: Failed to initialize ValidationEngine: %s", e)
        return

    # --- Print Results Table ---
    logger.info("%-25s | %-50s", "AnCora Group", "Declared Essential Head (for Lax Validation)")
    logger.info("%s-|--%s", "-" * 25, "-" * 50)
    for node_label, config in sorted(engine.rules.items()):
        if config.get("type", "group") == "group":
            head_leaves = config.get("head_leaves", [])
            head_str = ", ".join(head_leaves) if head_leaves else "(none defined)"
            logger.info("%-25s | %s", node_label, head_str)

    logger.info("=" * 80)


if __name__ == "__main__":
    report_declared_heads()
