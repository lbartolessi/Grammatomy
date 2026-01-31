import pytest
from anytree import RenderTree
from grammatomy.parsers import LispParser


def test_simple_parsing():
    # (S (NP Juan) (VP vino)) - Simplified structure
    lisp_str = "(S (NP Juan) (VP vino))"
    root = LispParser.to_anytree(lisp_str)

    assert root is not None
    assert root.label == "S"
    assert len(root.children) == 2
    assert root.children[0].label == "NP"
    assert root.children[0].word == "Juan"
    assert root.children[0].pos == "NP"  # In this simplified form, label acts as POS


def test_nested_parsing():
    # Standard PTB: (S (NP (NNP Juan)) (VP (VBD vino)))
    lisp_str = "(S (NP (NNP Juan)) (VP (VBD vino)))"
    root = LispParser.to_anytree(lisp_str)

    assert root is not None
    assert root.label == "S"
    # Check NP branch
    np_node = root.children[0]
    assert np_node.label == "NP"
    assert np_node.word is None  # Internal node

    nnp_node = np_node.children[0]
    assert nnp_node.label == "NNP"
    assert nnp_node.word == "Juan"
    assert nnp_node.pos == "NNP"


def test_deep_recursion():
    lisp_str = "(TOP (S (SN (NP (N Juan))) (VP (V vino) (SP (PREP a) (SN (N casa))))))"
    root = LispParser.to_anytree(lisp_str)
    assert root is not None
    assert root.label == "TOP"
    s_node = root.children[0]
    assert s_node.label == "S"

    # Verify leaf "casa"
    # Path: TOP -> S -> VP -> SP -> SN -> N -> casa
    vp = s_node.children[1]
    sp = vp.children[1]
    sn = sp.children[1]
    n = sn.children[0]
    assert n.word == "casa"
