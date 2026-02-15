import unittest

from anytree import Node, RenderTree

from core.grammatomy import from_ptb, to_ptb


class TestPTBConversion(unittest.TestCase):

    def test_simple_round_trip(self):
        """Verifies basic structure preservation using YAML-defined tags."""
        # Original Tree using AnCora/UD: (S (sn Juan) (grup.verb duerme))
        root = Node("S")
        sn = Node("sn", parent=root)
        Node("Juan", parent=sn)
        gv = Node("grup.verb", parent=root)
        Node("duerme", parent=gv)

        ptb_str = to_ptb(root)
        reconstructed_root = from_ptb(ptb_str)
        self.assertIsNotNone(reconstructed_root)
        if reconstructed_root is None:
            return

        # Helper to extract structure only (ignoring class types and extra attributes)
        def get_structure_str(start_node):
            return "\n".join(f"{pre}{node.name}" for pre, _, node in RenderTree(start_node))

        # Verify structure matches
        self.assertEqual(
            get_structure_str(root),
            get_structure_str(reconstructed_root),
            "Reconstructed tree structure differs from original",
        )

        # Verify idempotency (Round Trip String Equality)
        self.assertEqual(to_ptb(reconstructed_root), ptb_str)

    def test_parenthesis_sanitization(self):
        """Verifies that parentheses in text are handled correctly using POS tags."""
        # Sentence: "Hola (mundo)" -> with explicit POS for each word
        root = Node("S")
        # Each terminal word needs a POS tag as parent
        hola_pos = Node("NOUN", parent=root)
        Node("Hola", parent=hola_pos)

        lrb_pos = Node("PUNCT", parent=root)
        Node("(", parent=lrb_pos)  # Will be sanitized to -LRB-

        mundo_pos = Node("NOUN", parent=root)
        Node("mundo", parent=mundo_pos)

        rrb_pos = Node("PUNCT", parent=root)
        Node(")", parent=rrb_pos)  # Will be sanitized to -RRB-

        ptb_str = to_ptb(root)
        self.assertIn("-LRB-", ptb_str)
        self.assertIn("-RRB-", ptb_str)

        reconstructed = from_ptb(ptb_str)
        self.assertIsNotNone(reconstructed)

        # Check if leaves are back to normal
        leaves = [node.name for node in reconstructed.leaves] if reconstructed else []
        self.assertIn("(", leaves)
        self.assertIn(")", leaves)


if __name__ == "__main__":
    unittest.main()
