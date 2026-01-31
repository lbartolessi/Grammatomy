import json
from grammatomy.parsers.lisp_parser import SyntaxNode
from grammatomy import to_json

def test_json_export_structure():
    """
    Verifies that to_json correctly serializes SyntaxNode custom attributes
    (label, word, pos) into the JSON output.
    """
    # Manually construct a small tree: (S (NP Juan))
    root = SyntaxNode("S", label="S")
    child = SyntaxNode("NP", parent=root, label="NP", word="Juan", pos="NNP")
    
    json_str = to_json(root)
    data = json.loads(json_str)
    
    # Check root
    assert data["name"] == "S"
    assert data["label"] == "S"
    # Check children
    assert len(data["children"]) == 1
    assert data["children"][0]["word"] == "Juan"
    assert data["children"][0]["pos"] == "NNP"