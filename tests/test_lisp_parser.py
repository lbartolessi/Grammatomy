from core.grammatomy.parsers import LispParser


def test_simple_parsing():
    # (S (sn Juan) (grup.verb vino)) - AnCora structure aligned with YAML
    lisp_str = "(S (sn Juan) (grup.verb vino))"
    root = LispParser.to_anytree(lisp_str)

    assert root is not None
    assert root.label == "S"
    assert len(root.children) == 2
    assert root.children[0].label == "sn"
    assert root.children[0].word == "Juan"
    assert root.children[0].pos == "sn"  # In this simplified form, label acts as POS


def test_nested_parsing():
    # AnCora + UD: (S (sn (PROPN Juan)) (grup.verb (VERB vino)))
    lisp_str = "(S (sn (PROPN Juan)) (grup.verb (VERB vino)))"
    root = LispParser.to_anytree(lisp_str)

    assert root is not None
    assert root.label == "S"
    # Check sn branch
    sn_node = root.children[0]
    assert sn_node.label == "sn"
    assert sn_node.word is None  # Internal node

    propn_node = sn_node.children[0]
    assert propn_node.label == "PROPN"
    assert propn_node.word == "Juan"
    assert propn_node.pos == "PROPN"


def test_deep_recursion():
    lisp_str = "(sentence (S (sn (grup.nom (n Juan))) (grup.verb (v vino) (sp (prep a) (sn (grup.nom (n casa)))))))"
    root = LispParser.to_anytree(lisp_str)
    assert root is not None
    assert root.label == "sentence"
    s_node = root.children[0]
    assert s_node.label == "S"

    # Verify leaf "casa"
    # Path: sentence -> S -> grup.verb -> sp -> sn -> grup.nom -> n -> casa
    grup_verb = s_node.children[1]
    sp = grup_verb.children[1]
    sn = sp.children[1]
    grup_nom = sn.children[0]
    n = grup_nom.children[0]
    assert n.word == "casa"
