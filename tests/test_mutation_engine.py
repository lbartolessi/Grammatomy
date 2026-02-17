import unittest

from core.grammatomy.mutation import MutationEngine


class TestMutationEngine(unittest.TestCase):
    """
    Test suite for the MutationEngine.
    Verifies surgical operations: Detach, Reabsorb, Delete.
    """

    def test_detach_reabsorb_cycle(self):
        """
        Verifies that detaching a node and reabsorbing it restores the original state.
        """
        original_ptb = "(ROOT (sentence (sn (n Gato)) (grup.verb (v come))))"

        # 1. Detach 'sn' (path: 0 -> 0)
        # Path logic with VIRTUAL_ROOT wrapper:
        # VIRTUAL_ROOT (implicit) -> index 0 -> ROOT
        # ROOT -> index 0 -> sentence
        # sentence -> index 0 -> sn

        detach_result = MutationEngine.detach(
            main_ptb=original_ptb,
            node_path=[0, 0, 0],
            fragment_label="A",
            parent_context_label="sentence",
            target_label="sn",
        )

        main_after_detach = detach_result["main_ptb"]
        fragment_ptb = detach_result["fragment_ptb"]

        self.assertIn("LINK-A", main_after_detach)
        self.assertNotIn("Gato", main_after_detach)
        self.assertIn("Gato", fragment_ptb)

        # 2. Reabsorb
        reabsorb_result = MutationEngine.reabsorb(
            main_ptb=main_after_detach, fragment_ptb=fragment_ptb, link_label="A"
        )

        final_ptb = reabsorb_result["ptb"]

        # Normalize and compare
        def normalize(s):
            return s.replace(" ", "").replace("\n", "")

        self.assertEqual(normalize(original_ptb), normalize(final_ptb))

    def test_delete_node(self):
        """Test node deletion logic."""
        original_ptb = "(ROOT (sentence (sn (n Gato)) (grup.verb (v come))))"

        # Delete 'sn' (index 2 in PreOrder traversal?)
        # PreOrder: ROOT, sentence, sn, n, Gato, grup.verb, v, come
        # Indices: 0, 1, 2, ...
        # Let's delete 'sn' at index 2

        result = MutationEngine.delete_node(original_ptb, node_index=2)
        new_ptb = result["ptb"]

        self.assertNotIn("Gato", new_ptb)
        self.assertIn("grup.verb", new_ptb)


if __name__ == "__main__":
    unittest.main()
