import pytest
from anytree import RenderTree
from grammatomy import get_syntax_tree

@pytest.mark.slow
def test_spacy_integration_spanish():
    """
    Integration test using a Spanish model (via Hugging Face) to verify the spaCy+Benepar pipeline.
    Downloads model -> Parses -> Returns AnyTree.
    """
    # A sentence with some structure: Subject, Verb, Subordinate Clause
    text = "El científico confirmó que los resultados contradicen las teorías anteriores."
    
    params = {
        "engine": "spacy",
        "lang": "es",
        "model_package": "default", # Maps to 'benepar_en3' (fallback) in SpacyEngine
        "use_gpu": False
    }
    
    root = get_syntax_tree(text, params)
    
    print("\n" + "="*20 + " TREE VISUALIZATION (spaCy/Benepar) " + "="*20)
    if root:
        for pre, _, node in RenderTree(root):
            if hasattr(node, "word") and node.word:
                print(f"{pre}{node.name}: \"{node.word}\"")
            else:
                print(f"{pre}{node.name}")
    print("="*60)

    assert root is not None
    assert len(root.children) > 0
    assert any(node.word == "científico" for node in root.descendants)

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])