import unittest
from pathlib import Path

from src.core.grammatomy.validation_engine import ValidationEngine

# Path to the real rules file
RULES_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "core"
    / "grammatomy"
    / "assets"
    / "rules"
    / "hybrid_rules.yaml"
)


class TestValidationEngine(unittest.TestCase):
    def setUp(self):
        # Clear singleton cache to ensure fresh start
        ValidationEngine._instances = {}
        self.validator = ValidationEngine(str(RULES_PATH), "es")

    def test_initialization(self):
        """Test that the engine loads rules correctly."""
        self.assertTrue(self.validator._initialized)
        self.assertIn("sn", self.validator.rules)
        self.assertIn("grup.nom", self.validator.rules)

    def test_validate_sn_strict_mode(self):
        """
        Test strict validation for SN.
        Updated to reflect Hybrid Grammar: 'inc' is now a valid child.
        """
        # Valid case: Standard SN
        valid, errors, _ = self.validator.validate_node(
            "sn", ["spec", "grup.nom"], strategy="strict"
        )
        self.assertTrue(valid, f"Standard SN should be valid. Errors: {errors}")

        # Valid case: Hybrid SN with Inciso (Previously Invalid, now Valid)
        valid, errors, _ = self.validator.validate_node("sn", ["inc"], strategy="strict")
        self.assertTrue(valid, "SN -> INC should be valid in Hybrid Grammar.")

        # Invalid case: Random verb inside SN (still invalid)
        valid, errors, _ = self.validator.validate_node("sn", ["grup.verb"], strategy="strict")
        self.assertFalse(valid, "SN -> GRUP.VERB should be invalid.")

    def test_validate_sn_lax_mode(self):
        """Test lax validation (content presence)."""
        # Valid: Has mandatory grup.nom
        valid, errors, _ = self.validator.validate_node("sn", ["spec", "grup.nom"], strategy="lax")
        self.assertTrue(valid)

        # Valid: 'inc' is allowed and assumed to potentially contain mandatory content
        # due to permissive recursion in _check_yield_presence for non-leaf nodes.
        valid, errors, _ = self.validator.validate_node("sn", ["inc"], strategy="lax")
        self.assertTrue(valid)

    def test_can_add_child(self):
        """Test context compatibility."""
        # SN allows grup.nom
        valid, _ = self.validator.can_add_child("sn", "grup.nom")
        self.assertTrue(valid)

        # SN allows inc (New)
        valid, _ = self.validator.can_add_child("sn", "inc")
        self.assertTrue(valid)

        # SN does not allow grup.verb
        valid, _ = self.validator.can_add_child("sn", "grup.verb")
        self.assertFalse(valid)

        # Punctuation is always allowed
        valid, _ = self.validator.can_add_child("sn", "PUNCT")
        self.assertTrue(valid)

    def test_get_valid_substitutions(self):
        """Test substitution suggestions."""
        # Case 1: Context compatible with 'S' (contains verb)
        subs_verb = self.validator.get_valid_substitutions("sentence", ["grup.verb"])
        self.assertIn("S", subs_verb)
        # 'sn' cannot directly contain 'grup.verb', so it shouldn't be here
        self.assertNotIn("sn", subs_verb)

        # Case 2: Context compatible with 'sn' (contains nominal group)
        subs_noun = self.validator.get_valid_substitutions("sentence", ["grup.nom"])
        self.assertIn("sn", subs_noun)

    def test_legacy_tag_warning(self):
        """Ensure legacy tags are not present in compiled rules."""
        # This assumes compile_rules.py has run and removed 'n', 'v', etc.
        sn_allowed = self.validator.allowed_children.get("sn", set())
        self.assertNotIn("n", sn_allowed)
        self.assertNotIn("v", sn_allowed)

    def test_gapping_patterns(self):
        """Verify new gapping patterns in Sentence."""
        # Pattern: [sn, grup.verb, sn, conj, sn]
        children = ["sn", "grup.verb", "sn", "conj", "sn"]
        valid, errors, _ = self.validator.validate_node("sentence", children, strategy="strict")
        self.assertTrue(valid, f"Gapping pattern should be valid. Errors: {errors}")

    def test_enumeration_patterns(self):
        """Verify enumeration patterns in SN."""
        # Pattern: [sn, f, sn, conj, sn] -> [sn, PUNCT, sn, conj, sn]
        # Note: PUNCT is filtered out in strict pattern check, so we check [sn, sn, conj, sn]
        children = ["sn", "PUNCT", "sn", "conj", "sn"]
        valid, errors, _ = self.validator.validate_node("sn", children, strategy="strict")
        self.assertTrue(valid, f"Enumeration pattern should be valid. Errors: {errors}")

    def test_copulative_sentence(self):
        """Verify copulative sentence pattern."""
        # Pattern: [sn, grup.verb, s.a]
        children = ["sn", "grup.verb", "s.a"]
        valid, errors, _ = self.validator.validate_node("sentence", children, strategy="strict")
        self.assertTrue(valid, f"Copulative pattern should be valid. Errors: {errors}")


if __name__ == "__main__":
    unittest.main()
