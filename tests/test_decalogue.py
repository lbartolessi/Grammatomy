import pytest
from anytree import Node, RenderTree


# Mocking the Validator logic for the purpose of the test suite structure
# In a real scenario, this would import the actual Validator class from src.core
class Validator:
    def __init__(self, mode="lax"):
        self.mode = mode

    def validate_structure(self, node):
        """
        Validates a single node against the rules.
        Returns (bool, list_of_errors)
        """
        errors = []

        # Rule: Root cannot be deleted (Logic handled by Editor, but structure must be valid)
        # Here we validate parent-child relationships

        # SN Validation
        if node.name == "sn":
            children_names = [c.name for c in node.children]
            has_grup_nom = "grup.nom" in children_names
            # In a real tree, leaves would have POS tags like 'NOUN', here we simplify checking names
            has_noun_child = any(c.name.startswith("NOUN") for c in node.children)

            if self.mode == "strict":
                if not has_grup_nom:
                    errors.append("Strict Mode Violation: 'sn' must contain 'grup.nom'")
            elif self.mode == "lax":
                if not has_grup_nom and not has_noun_child:
                    errors.append(
                        "Lax Mode Violation: 'sn' must contain 'grup.nom' or direct 'NOUN'"
                    )

        # Grup.Nom Validation
        if node.name == "grup.nom":
            # Check for head
            has_head = any(c.name in ["NOUN", "PROPN", "PRON"] for c in node.children)
            if not has_head:
                errors.append(f"Violation: 'grup.nom' requires a nominal head")

        return len(errors) == 0, errors

    def can_delete(self, node):
        """
        Decalogue Rule: Root cannot be deleted.
        """
        if node.is_root:
            return False
        return True

    def validate_ghost_mutation(self, ghost_node, new_label, parent_label):
        """
        Decalogue Rule: Ghost nodes must mutate to allowed types.
        """
        # Simplified logic for demonstration
        allowed_map = {
            "sn": ["grup.nom", "spec"],
            "grup.nom": ["NOUN", "ADJ", "S", "sp"],
            "S": ["sn", "grup.verb", "sp"],
        }

        if parent_label in allowed_map:
            return new_label in allowed_map[parent_label]
        return True  # Allow if parent not defined in strict map for now


@pytest.fixture
def strict_validator():
    return Validator(mode="strict")


@pytest.fixture
def lax_validator():
    return Validator(mode="lax")


class TestDecalogue:
    """
    The Decalogue Regression Suite ensures that the core editing policies
    (The "Constitution" of Grammatomy) are never violated.
    """

    def test_root_immutability(self, lax_validator):
        """Rule: The Root Node cannot be deleted."""
        root = Node("ROOT")
        child = Node("S", parent=root)

        assert lax_validator.can_delete(child) is True
        assert lax_validator.can_delete(root) is False

    def test_sn_structure_strict(self, strict_validator):
        """
        Strict Mode: SN must have grup.nom (AnCora X-Bar compliance).
        """
        # Invalid Strict Structure: sn -> NOUN (Collapsed)
        sn = Node("sn")
        noun = Node("NOUN", parent=sn)

        is_valid, errors = strict_validator.validate_structure(sn)
        assert is_valid is False
        assert "Strict Mode Violation" in errors[0]

        # Valid Strict Structure: sn -> grup.nom -> NOUN
        sn_valid = Node("sn")
        gn = Node("grup.nom", parent=sn_valid)
        noun_valid = Node("NOUN", parent=gn)

        is_valid, _ = strict_validator.validate_structure(sn_valid)
        assert is_valid is True

    def test_sn_structure_lax(self, lax_validator):
        """
        Lax Mode: SN can collapse grup.nom (Neural Parser compliance).
        """
        # Valid Lax Structure: sn -> NOUN
        sn = Node("sn")
        noun = Node("NOUN", parent=sn)

        is_valid, errors = lax_validator.validate_structure(sn)
        assert is_valid is True
        assert len(errors) == 0

    def test_ghost_mutation_rules(self, strict_validator):
        """
        Rule: Ghost nodes can only mutate into allowed children of their parent.
        """
        # Context: Parent is 'sn'
        # Allowed: 'grup.nom', 'spec'
        # Forbidden: 'VERB' (Verbs don't go directly in SN in AnCora)

        ghost = Node("GHOST")  # Parent implied as 'sn' for the test logic

        # Attempt to mutate to 'grup.nom' (Allowed)
        assert strict_validator.validate_ghost_mutation(ghost, "grup.nom", "sn") is True

        # Attempt to mutate to 'VERB' (Forbidden)
        assert strict_validator.validate_ghost_mutation(ghost, "VERB", "sn") is False
