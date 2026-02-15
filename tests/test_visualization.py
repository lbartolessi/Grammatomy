import pytest
from anytree import Node

from core.grammatomy.visualization.ascii_renderer import render_ascii_colored
from core.grammatomy.visualization.graphviz_renderer import get_graphviz_dot
from core.grammatomy.visualization.json_renderer import render_json_colored
from core.grammatomy.visualization.lisp_renderer import render_lisp_colored


@pytest.fixture
def visual_tree():
    """Creates a standard tree for rendering tests using YAML-defined tags."""
    # (S (sn (spec Det) (n cat)) (grup.verb (v sat)) (PUNCT .))
    # Note: terminal nodes (words) are direct children in this representation
    root = Node("S")
    sn = Node("sn", parent=root)
    spec = Node("spec", parent=sn)
    spec.word = "The"
    n = Node("n", parent=sn)
    n.word = "cat"
    gv = Node("grup.verb", parent=root)
    v = Node("v", parent=gv)
    v.word = "sat"
    # Add a punctuation node
    punct = Node("PUNCT", parent=root)
    punct.word = "."
    return root


def test_ascii_renderer(visual_tree):
    html = render_ascii_colored(visual_tree)
    assert "S" in html
    assert "spec" in html
    assert "The" in html
    assert "." in html


def test_graphviz_renderer(visual_tree):
    dot_code = get_graphviz_dot(visual_tree)
    # Check structure: labels for nodes should be present
    assert 'label="S"' in dot_code  # Root
    assert 'label="sn"' in dot_code  # sn phrase
    assert 'label="spec"' in dot_code  # specifier
    assert 'label="n"' in dot_code  # noun tag
    assert 'label="PUNCT"' in dot_code  # punctuation
    # Verify colors are applied (shape and fillcolor present)
    assert "shape=" in dot_code
    assert "fillcolor=" in dot_code


def test_json_renderer(visual_tree):
    html = render_json_colored(visual_tree)
    assert "<span class='style-phrasal'>\"S\"</span>" in html
    assert (
        "<span class='style-pos'>\"spec\"</span>" in html
        or "<span class='style-pos'>\"sn\"</span>" in html
    )
    assert "<span class='style-word'>\"The\"</span>" in html or "The" in html
    # Punctuation is in the JSON structure
    assert '"."' in html or "\\u002e" in html
    assert "<span class='tree-connector'>\"children\":</span> [" in html


def test_lisp_renderer(visual_tree):
    html = render_lisp_colored(visual_tree)
    assert "<span class='style-phrasal'>S</span>" in html
    assert (
        "<span class='style-pos'>spec</span>" in html or "<span class='style-pos'>n</span>" in html
    )
    assert "<span class='style-word'>\"The\"</span>" in html or "The" in html
    assert "<span class='style-punct'>.</span>" in html or "PUNCT" in html
    assert "<div>&nbsp;&nbsp;&nbsp;&nbsp;<span class='tree-connector'>(</span>" in html
