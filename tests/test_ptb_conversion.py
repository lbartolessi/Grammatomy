import unittest

from anytree import Node, RenderTree

from core.grammatomy import from_ptb, to_ptb


class TestPTBConversion(unittest.TestCase):

    def test_simple_round_trip(self):
        """Verifies basic structure preservation."""
        # Original Tree: (S (NP Juan) (VP duerme))
        root = Node("S")
        np = Node("NP", parent=root)
        Node("Juan", parent=np)
        vp = Node("VP", parent=root)
        Node("duerme", parent=vp)

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
        """Verifies that parentheses in text are handled correctly."""
        # Sentence: "Hola (mundo)" -> Tree should preserve parens in content
        root = Node("S")
        Node("Hola", parent=root)
        Node("(", parent=root)  # Should become -LRB- in PTB
        Node("mundo", parent=root)
        Node(")", parent=root)  # Should become -RRB- in PTB

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
