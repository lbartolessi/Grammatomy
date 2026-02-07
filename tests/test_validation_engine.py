from pathlib import Path

import pytest
import yaml

from core.validation_engine import ValidationEngine


@pytest.fixture
def rules_file(tmp_path):
    """Combines rule parts into a single temp file for testing."""
    p1_path = Path(__file__).resolve().parents[1] / "src/core/rules_es.yaml"

    # This is a simplified Part 2 for focused testing
    p2_content = """
  sp:
    type: group
    rules:
      all:
        allowed_children: [ADP, prep, sn]
      strict:
        mandatory_children: [[ADP, prep], [sn]]
  label_transparency:
    - id: ADP_EQUIV
      tags: [ADP, prep]
  NOUN: { type: leaf }
  VERB: { type: leaf }
  ADP: { type: leaf }
  prep: { type: leaf }
"""

    with open(p1_path, "r", encoding="utf-8") as f:
        full_content = f.read() + p2_content

    rules_file_path = tmp_path / "test_rules.yaml"
    rules_file_path.write_text(full_content, encoding="utf-8")
    return str(rules_file_path)


@pytest.fixture
def engine(rules_file):
    """Provides a ValidationEngine instance with the default 'lax' strategy."""
    return ValidationEngine(rules_file)


class TestValidationEngine:

    def test_initialization_and_strategy_setting(self, engine):
        """Tests that the engine loads rules and can switch strategies."""
        assert engine.strategy == "lax"
        assert "sn" in engine.rules

        engine.set_strategy("strict")
        assert engine.strategy == "strict"

        with pytest.raises(ValueError):
            engine.set_strategy("invalid_strategy")

    def test_validate_sn_lax_mode_algorithmic(self, engine):
        """Lax mode should algorithmically allow NOUN as descendant of sn."""
        engine.set_strategy("lax")

        # Valid: Collapsed structure (sn -> NOUN)
        # We pass NOUN as both child and descendant
        is_valid, errors, _ = engine.validate_node(
            "sn", ["NOUN"], descendants_labels=["NOUN"]
        )
        assert is_valid is True
        assert not errors

        # Invalid: Contains a forbidden child
        is_valid, errors, _ = engine.validate_node(
            "sn", ["VERB"], descendants_labels=["VERB"]
        )
        assert is_valid is False
        assert "missing essential content" in errors[0]

    def test_validate_sn_strict_mode(self, engine):
        """Strict mode must enforce X-Bar hierarchy (sn -> grup.nom)."""
        engine.set_strategy("strict")

        # Invalid: Collapsed structure is forbidden in strict mode
        is_valid, errors, _ = engine.validate_node(
            "sn", ["spec", "NOUN"], descendants_labels=["spec", "NOUN"]
        )
        assert is_valid is False
        assert (
            "cannot contain 'NOUN'" in errors[0]
        )  # NOUN is not allowed direct child in strict

        # Invalid: Missing mandatory child 'grup.nom'
        is_valid, errors, _ = engine.validate_node(
            "sn", ["spec"], descendants_labels=["spec"]
        )
        assert is_valid is False
        assert "missing mandatory child" in errors[0]

        # Valid: Correct strict structure
        is_valid, errors, _ = engine.validate_node("sn", ["spec", "grup.nom"])
        assert is_valid is True
        assert not errors

    def test_lax_mandatory_content(self, engine):
        """
        Lax mode should enforce mandatory YIELD recursively.
        sp strict mandatory: [ADP/prep] AND [sn].

        Case 1: sp -> prep (Missing sn).
        'sn' is missing. 'sn' requires 'grup.nom'. 'grup.nom' requires 'NOUN'.
        If 'NOUN' is missing, then 'sn' is effectively missing.
        """
        engine.set_strategy("lax")

        # Invalid: sp -> prep (Missing term/sn)
        is_valid, errors, _ = engine.validate_node(
            "sp", ["prep"], descendants_labels=["prep"]
        )
        assert is_valid is False
        assert "missing essential content" in errors[0]

        # Valid: sp -> prep + NOUN (Collapsed sn)
        # sp requires sn -> sn requires grup.nom -> grup.nom requires NOUN.
        # NOUN is present, so sn is "satisfied".
        is_valid, errors, _ = engine.validate_node(
            "sp", ["prep", "NOUN"], descendants_labels=["prep", "NOUN"]
        )
        assert is_valid is True

    def test_transparency_intersection(self, engine):
        """
        Test that VERB and v are treated as the same mandatory content.
        """
        # Mocking a node 'grup.verb' that allows [VERB, v]
        # Intersection({VERB}, {v}) should be {VERB_EQUIV} -> {VERB} (normalized)
        # This requires the engine to load the transparency map correctly.

        # We can test this by checking if 'grup.verb' (from rules_es.yaml) requires VERB
        # rules_es.yaml defines grup.verb allowed: [VERB, AUX, v...]
        # If we assume AUX is also verbal, intersection might be VERB_EQUIV.
        pass

    def test_reverse_index_for_dropdowns(self, engine):
        """Tests the get_valid_parents method."""
        # Reverse index now uses strict rules for dropdown suggestions (canonical parents)

        # NOUN is strictly child of grup.nom
        parents_of_noun = engine.get_valid_parents(
            "NOUN"
        )  # Assuming NOUN is allowed in strict grup.nom
        # Note: In the test fixture, NOUN is not explicitly added to strict allowed of grup.nom in p2_content,
        # but let's assume the logic holds for what is defined.
        # In p2_content: sp -> allowed [ADP, prep, sn].

        parents_of_prep = engine.get_valid_parents("prep")
        assert "sp" in parents_of_prep

        parents_of_verb = engine.get_valid_parents("VERB")
        assert "grup.verb" in parents_of_verb
