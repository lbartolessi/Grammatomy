from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from grammatomy.parsers.lisp_parser import SyntaxNode

from src.api.app.main import app

client = TestClient(app)

# --- Mock Data ---
MOCK_TEXT = "El veloz murciélago."
# Construct a simple tree: (S (NP El) (VP ...))
MOCK_ROOT = SyntaxNode("S")
np = SyntaxNode("NP", parent=MOCK_ROOT)
SyntaxNode("Det", parent=np, word="El")
vp = SyntaxNode("VP", parent=MOCK_ROOT)
SyntaxNode("V", parent=vp, word="come")

# Attach the raw lisp string as expected by the /render/lisp endpoint
MOCK_ROOT.raw_lisp = "(S (NP (Det El)) (VP (V come)))"


@pytest.fixture
def mock_parser():
    """Mocks the core parsing logic to avoid loading heavy models."""
    with patch("src.api.app.main.get_syntax_tree") as mock:
        mock.return_value = MOCK_ROOT
        yield mock


@pytest.fixture
def mock_graphviz():
    """Mocks graphviz generation and piping."""
    with patch(
        "src.api.app.main.get_graphviz_dot", return_value="digraph G {}"
    ) as mock_dot:
        with patch(
            "graphviz.Source.pipe", return_value=b"\x89PNG\r\n\x1a\n"
        ) as mock_pipe:
            yield mock_dot, mock_pipe


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Grammatomy API" in response.json()["message"]


def test_parse_endpoint_success(mock_parser):  # pylint: disable=redefined-outer-name
    payload = {"text": MOCK_TEXT, "engine": "stanza", "lang": "es"}
    response = client.post("/api/parse", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert data["meta"]["status"] == "success"
    assert data["root"]["label"] == "S"
    assert len(data["root"]["children"]) == 2

    # Verify mock call
    mock_parser.assert_called_once()
    args, kwargs = mock_parser.call_args
    assert args[0] == MOCK_TEXT
    assert kwargs["params"]["engine"] == "stanza"


def test_parse_endpoint_failure(mock_parser):  # pylint: disable=redefined-outer-name
    # Simulate parser returning None (e.g. empty input or model failure)
    mock_parser.return_value = None

    payload = {"text": "Fail me"}
    response = client.post("/api/parse", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["status"] == "failed"
    assert data["root"] is None
    assert "Parser returned no tree" in data["error"]


def test_render_ascii(
    mock_parser,
):  # pylint: disable=redefined-outer-name, unused-argument
    payload = {"text": MOCK_TEXT}
    response = client.post("/api/render/ascii", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    # Check for tree structure in text
    assert "S" in response.text
    assert "NP" in response.text
    assert "class='style-word'>\"El\"</span>" in response.text


def test_render_json(
    mock_parser,
):  # pylint: disable=redefined-outer-name, unused-argument
    payload = {"text": MOCK_TEXT}
    response = client.post("/api/render/json", json=payload)

    assert response.status_code == 200
    data = response.json()
    # Should return the node directly
    assert data["label"] == "S"
    assert "children" in data
    assert "meta" not in data  # Ensure it's not wrapped in ParseResponse


def test_render_lisp(
    mock_parser,
):  # pylint: disable=redefined-outer-name, unused-argument
    payload = {"text": MOCK_TEXT}
    response = client.post("/api/render/lisp", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == MOCK_ROOT.raw_lisp


def test_render_graphviz(
    mock_parser, mock_graphviz
):  # pylint: disable=redefined-outer-name, unused-argument
    payload = {"text": MOCK_TEXT}
    response = client.post("/api/render/graphviz", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"\x89PNG\r\n\x1a\n"


def test_render_lisp_missing_attr(mock_parser):  # pylint: disable=redefined-outer-name
    # Simulate a node without raw_lisp attribute
    mock_node_no_lisp = SyntaxNode("ROOT")
    mock_parser.return_value = mock_node_no_lisp

    payload = {"text": MOCK_TEXT}
    response = client.post("/api/render/lisp", json=payload)

    assert response.status_code == 404
    assert "Original LISP string not available" in response.json()["detail"]
