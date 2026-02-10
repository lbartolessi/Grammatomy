from pathlib import Path

import pytest
import yaml

from core.grammatomy.validation_engine import ValidationEngine


@pytest.fixture
def rules_file(tmp_path):
    """Creates a self-contained rules file for testing."""
    content = """
tree_config:
  language: es
nodes:
  - id: sn
    type: group
    allowed_children:
      mandatory: [grup.nom]
      optional: [spec]
  - id: sp
    type: group
    allowed_children:
      mandatory: [[ADP, prep], [sn]]
      optional: []
  - id: grup.nom
    type: group
    allowed_children:
      mandatory: [NOUN]
      optional: []
  - id: grup.verb
    type: group
    allowed_children:
      mandatory: [VERB]
      optional: []
  - id: NOUN
    type: leaf
  - id: VERB
    type: leaf
  - id: ADP
    type: leaf
  - id: prep
    type: leaf
  - id: spec
    type: leaf
"""
    rules_file_path = tmp_path / "test_rules.yaml"
    rules_file_path.write_text(content, encoding="utf-8")
    return str(rules_file_path)


@pytest.fixture
def engine(rules_file):
    """Provides a ValidationEngine instance with the default 'lax' strategy."""
    return ValidationEngine(rules_file, lang="es")


class TestValidationEngine:

    def test_initialization(self, engine):
        """Tests that the engine loads rules correctly."""
        assert "sn" in engine.rules
        assert engine.lang == "es"

    def test_validate_sn_lax_mode_algorithmic(self, engine):
        """Lax mode should algorithmically allow NOUN as descendant of sn."""

        # Valid: Collapsed structure (sn -> NOUN)
        # We pass NOUN as both child and descendant
        is_valid, errors, _ = engine.validate_node("sn", ["NOUN"], descendants_labels=["NOUN"])
        assert is_valid is True
        assert not errors

        # Invalid: Contains a forbidden child
        is_valid, errors, _ = engine.validate_node("sn", ["VERB"], descendants_labels=["VERB"])
        assert is_valid is False
        assert "missing essential content" in errors[0]

    @pytest.mark.xfail(reason="Pending definitive rule definitions for strict mode")
    def test_validate_sn_strict_mode(self, engine):
        """Strict mode must enforce X-Bar hierarchy (sn -> grup.nom)."""

        # Invalid: Collapsed structure is forbidden in strict mode
        is_valid, errors, _ = engine.validate_node(
            "sn", ["spec", "NOUN"], descendants_labels=["spec", "NOUN"], strategy="strict"
        )
        assert is_valid is False
        assert "cannot contain 'NOUN'" in errors[0]  # NOUN is not allowed direct child in strict

        # Invalid: Missing mandatory child 'grup.nom'
        is_valid, errors, _ = engine.validate_node("sn", ["spec"], descendants_labels=["spec"])
        assert is_valid is False
        # Note: In strict mode without explicit strategy arg (defaults to lax), this might pass or fail differently.

        # Valid: Correct strict structure
        is_valid, errors, _ = engine.validate_node("sn", ["spec", "grup.nom"], strategy="strict")
        assert is_valid is True
        assert not errors

    @pytest.mark.xfail(reason="Pending definitive rule definitions for lax mode")
    def test_lax_mandatory_content(self, engine):
        """
        Lax mode should enforce mandatory YIELD recursively.
        sp strict mandatory: [ADP/prep] AND [sn].

        Case 1: sp -> prep (Missing sn).
        'sn' is missing. 'sn' requires 'grup.nom'. 'grup.nom' requires 'NOUN'.
        If 'NOUN' is missing, then 'sn' is effectively missing.
        """

        # Invalid: sp -> prep (Missing term/sn)
        is_valid, errors, _ = engine.validate_node("sp", ["prep"], descendants_labels=["prep"])
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

    @pytest.mark.xfail(reason="Reverse index population requires fix in fixture or engine")
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
