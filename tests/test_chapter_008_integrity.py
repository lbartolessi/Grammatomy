import unittest

from anytree import PreOrderIter

from core.grammatomy import to_ptb
from src.core.grammatomy.parsers.lisp_parser import LispParser


class TestChapter008Integrity(unittest.TestCase):
    """
    Regression suite for Chapter 008: Visual Interface & Parser Hardening.
    Focuses on Leaf Integrity ('Gato Gato' bug) and Export Fidelity.
    """

    def setUp(self):
        self.parser = LispParser()

    def test_leaf_atomicity_gato_gato_fix(self):
        """
        CRITICAL: Verifies the fix for the 'Gato Gato' bug.
        A POS node (e.g., NN, n) must have exactly ONE child, which is the terminal word.
        It must NOT have the word as a child which then has the word again as a child.
        """
        # Input that previously caused issues (AnCora style)
        lisp_input = "(S (sn (grup.nom (n gato))))"

        root = self.parser.to_anytree(lisp_input)

        # Navigate to the 'n' node
        # Path: S -> sn -> grup.nom -> n
        # We use robust navigation to find the 'n' node regardless of exact path if possible,
        # but here we expect strict structure.
        assert root is not None
        n_node = root.children[0].children[0].children[0]

        # Assertions
        self.assertEqual(n_node.name, "n", "Target node should be 'n'")

        # 1. Check Child Count
        self.assertEqual(len(n_node.children), 1, "POS node 'n' must have exactly one child")

        # 2. Check Terminal Identity
        terminal = n_node.children[0]
        self.assertEqual(terminal.name, "gato", "Child must be the terminal 'gato'")
        self.assertTrue(terminal.is_leaf, "The terminal 'gato' must be a leaf")

        # 3. Check for Recursion (The Bug)
        # The bug was: n -> gato -> gato
        self.assertEqual(len(terminal.children), 0, "The terminal node must NOT have children")

    def test_complex_gongora_structure(self):
        """
        Verifies parsing of deep, recursive structures (Góngora Mode simulation).
        Ensures no data loss in deeply nested subtrees.
        """
        # A deeply nested structure simulating baroque syntax fragmentation
        gongora_lisp = (
            "(sentence (sn (spec (d El)) (grup.nom (n caminante))) "
            "(S (relatiu (p que)) (grup.verb (v busca) "
            "(sn (grup.nom (n huellas) (sp (prep (s de)) "
            "(sn (grup.nom (n pasos) (s.a (grup.a (a perdidos)))))))))))"
        )

        root = self.parser.to_anytree(gongora_lisp)

        # Verify depth and specific leaf retrieval
        leaves = [node.name for node in PreOrderIter(root) if node.is_leaf]
        expected_leaves = ["El", "caminante", "que", "busca", "huellas", "de", "pasos", "perdidos"]

        self.assertEqual(leaves, expected_leaves, "Deep structure parsing lost or scrambled leaves")

    def test_export_reconstruction_fidelity(self):
        """
        Verifies that a tree can be exported back to LISP without mutation.
        (Parse -> Export -> Compare)
        """
        original_lisp = "(S (sn (spec (d La)) (grup.nom (n verdad))) (grup.verb (v padece)))"

        # 1. Parse
        root = self.parser.to_anytree(original_lisp)
        assert root is not None

        # 2. Export (Reconstruct string)
        # Use the standard exporter
        exported_lisp = to_ptb(root)

        # Normalize strings (remove spaces for comparison)
        def normalize(s):
            return s.replace(" ", "").replace("\n", "")

        self.assertEqual(
            normalize(original_lisp),
            normalize(exported_lisp),
            "Exported LISP does not match original input. Reconstruction failed.",
        )


if __name__ == "__main__":
    unittest.main()
