import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from anytree import RenderTree

from core.grammatomy.parsers.lisp_parser import from_ptb


def test_ptb(ptb_string):
    print(f"\n--- Testing: {ptb_string} ---")
    try:
        root = from_ptb(ptb_string)
        for pre, fill, node in RenderTree(root):
            # Print name and number of children to detect duplicates
            print(f"{pre}{node.name} (children={len(node.children)})")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    print("Running duplication diagnostics...")

    # 1. Simple word (Standard)
    test_ptb("(PRON Estas)")

    # 2. Duplicated word in string (Malformation)
    test_ptb("(PRON Estas Estas)")

    # 3. Nested word (Alternative format)
    test_ptb("(PRON (Estas))")

    # 4. Complex case (From your example)
    complex_ptb = "(ROOT (sentence (grup.nom (grup.nom (PRON Estas) (S (relatiu (PRON que)) (sn (grup.nom (PRON me))) (grup.verb (VERB dictó)))) (PUNCT ,))))"
    test_ptb(complex_ptb)
