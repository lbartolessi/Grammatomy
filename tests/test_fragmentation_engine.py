import unittest

from core.grammatomy.fragmentation import FragmentationEngine


class TestFragmentationEngine(unittest.TestCase):
    """
    Test suite for the FragmentationEngine (Góngora Mode).
    Verifies automatic tree decomposition and reconstruction.
    """

    def setUp(self):
        self.engine = FragmentationEngine()

    def test_no_fragmentation_needed(self):
        """Test that simple trees without nested S are returned as is."""
        ptb = "(ROOT (sentence (sn (n Juan)) (grup.verb (v corre))))"
        main_ptb, subtrees, _ = self.engine.fragment(ptb)

        self.assertEqual(len(subtrees), 0)
        # Normalize strings for comparison (remove spaces)
        self.assertEqual(main_ptb.replace(" ", ""), ptb.replace(" ", ""))

    def test_basic_fragmentation(self):
        """Test extraction of a single nested S node."""
        # (ROOT (sentence (S (sn (n Maria)) (grup.verb (v come)))))
        # The inner S should be extracted if it meets criteria (e.g. word count > 2)
        ptb = "(ROOT (sentence (S (sn (n Maria)) (grup.verb (v come) (sn (n pan))))))"

        main_ptb, subtrees, integrity = self.engine.fragment(ptb)

        self.assertEqual(len(subtrees), 1)
        self.assertTrue("LINK-A" in main_ptb)
        self.assertEqual(subtrees[0]["label"], "A")

        # Verify reconstruction
        reconstructed = self.engine.defragment(main_ptb, subtrees)
        self.assertIn("Maria", reconstructed)
        self.assertIn("pan", reconstructed)
        self.assertNotIn("LINK-A", reconstructed)

        if integrity:
            self.assertEqual(integrity["status"], "passed")

    def test_nested_fragmentation_gongora(self):
        """Test recursive fragmentation (S inside S)."""
        # A structure deep enough to trigger multiple levels
        # S1 -> ... S2 -> ...
        ptb = (
            "(ROOT (sentence (S (sn (n Autor)) (grup.verb (v escribe) "
            "(S (sn (n Libro)) (grup.verb (v tiene) (sn (n Paginas))))))))"
        )

        main_ptb, subtrees, _ = self.engine.fragment(ptb)

        # Should extract multiple levels
        self.assertGreater(len(subtrees), 0)

        # Verify reconstruction
        reconstructed = self.engine.defragment(main_ptb, subtrees)
        # Basic check: original words are present
        self.assertIn("Autor", reconstructed)
        self.assertIn("Libro", reconstructed)
        self.assertIn("Paginas", reconstructed)

    def test_defragment_robustness_iteration_limit(self):
        """
        CRITICAL: Test the fix for the iteration limit (sn != LINK bug).
        We simulate a chain of dependencies longer than the old default (10).
        Chain: ROOT -> LINK-A -> LINK-B -> ... -> LINK-K -> Content
        """
        main_ptb = "(ROOT (sentence (LINK-A-000)))"
        subtrees = []

        # Chain A -> B -> C ... -> K (11 levels)
        labels = "ABCDEFGHIJK"
        for i in range(len(labels) - 1):
            current = labels[i]
            next_l = labels[i + 1]
            # Subtree A contains LINK-B
            ptb = f"(LINK-Main-000 (sentence (LINK-{next_l}-000)))"
            subtrees.append(
                {
                    "label": current,
                    "ptb": ptb,
                    "id": f"st_{current}",
                    "root_node_id": "0",
                }
            )

        # Last one K contains real content
        subtrees.append(
            {
                "label": "K",
                "ptb": "(LINK-J-000 (sentence (sn (n Final))))",
                "id": "st_K",
                "root_node_id": "0",
            }
        )

        # This requires at least 11 passes to resolve A->B->...->K->Content
        reconstructed = self.engine.defragment(main_ptb, subtrees)

        self.assertIn("Final", reconstructed)
        self.assertNotIn("LINK-", reconstructed)


if __name__ == "__main__":
    unittest.main()
