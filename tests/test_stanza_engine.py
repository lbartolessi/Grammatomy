import pytest
from anytree import RenderTree

from core.grammatomy import get_syntax_tree


@pytest.mark.slow
def test_stanza_integration_english():
    """
    Integration test using a small English model to verify the full pipeline.
    Downloads model -> Parses -> Returns AnyTree.
    """
    text = (
        "The scientist confirmed that the results, which were obtained after the "
        "experiment that the team conducted last year, significantly contradict "
        "the previous theories."
    )
    params = {
        "engine": "stanza",
        "lang": "en",
        "model_package": "default",  # 'gem' does not support constituency; 'default' uses WSJ
        "use_gpu": False,  # Force CPU for testing efficiency
    }

    root = get_syntax_tree(text, params)

    print("\n" + "=" * 20 + " TREE VISUALIZATION " + "=" * 20)
    if root:
        for pre, _, node in RenderTree(root):
            if hasattr(node, "word") and node.word:
                print(f'{pre}{node.name}: "{node.word}"')
            else:
                print(f"{pre}{node.name}")
    print("=" * 60)

    assert root is not None
    assert root.name == "ROOT" or root.name == "S"
    # Verify we have some structure
    assert len(root.children) > 0
    assert any(node.word == "scientist" for node in root.descendants)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
