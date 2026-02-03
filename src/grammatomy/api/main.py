import time

import graphviz
import torch
from anytree import Node, RenderTree
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from starlette.responses import JSONResponse

from grammatomy import get_syntax_tree
from grammatomy.visualization import get_graphviz_dot

from .schemas import ParseRequest, ParseResponse, SyntaxNode

app = FastAPI(
    title="Grammatomy API",
    description="Universal Constituent Parser Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

_PARSER_RETURNED_NO_TREE = (
    "Parser returned no tree. Check language/model compatibility."
)


@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception):
    """Catches any unhandled exception and returns a 500 Internal Server Error."""
    # In a production environment, you would log the exception here
    # import logging
    # logging.error(f"Unhandled exception for {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


def anytree_to_pydantic(node: Node) -> SyntaxNode:
    """
    Recursively converts an AnyTree Node to a Pydantic SyntaxNode.
    """
    # Extract attributes, excluding internal anytree fields
    # We filter out private attributes (starting with _)
    # which include anytree internals like _NodeMixin__children
    attrs = {
        k: v
        for k, v in node.__dict__.items()
        if k not in ["name", "parent", "children", "label", "word"]
        and not k.startswith("_")
    }

    return SyntaxNode(
        label=str(
            getattr(node, "label", node.name)
        ),  # Fallback to name if label missing
        word=getattr(node, "word", None),
        attributes=attrs,
        children=[anytree_to_pydantic(child) for child in node.children],
    )


def get_server_params(req: ParseRequest) -> dict:
    """Constructs execution parameters, determining hardware capabilities server-side."""
    return {
        "engine": req.engine,
        "lang": req.lang,
        "model_package": req.model_package,
        "use_gpu": torch.cuda.is_available(),
    }


@app.get("/")
async def root():
    return {"message": "Grammatomy API is running. Visit /docs for usage."}


@app.post("/parse", response_model=ParseResponse)
async def parse_sentence(req: ParseRequest):
    """
    Parses a sentence into a constituency tree using the specified engine.
    """
    params = get_server_params(req)
    start_time = time.time()

    # Execute core logic - unhandled exceptions will be caught by the global handler
    root_node = get_syntax_tree(req.text, params=params)
    elapsed = time.time() - start_time

    if not root_node:
        return ParseResponse(
            root=None,
            meta={"elapsed": elapsed, "status": "failed"},
            error="Parser returned no tree. Check language/model compatibility.",
        )

    # Convert to response schema
    tree_schema = anytree_to_pydantic(root_node)

    return ParseResponse(
        root=tree_schema,
        meta={
            "elapsed": elapsed,
            "status": "success",
            "engine": req.engine,
            "lang": req.lang,
        },
    )


@app.post("/render/ascii", response_class=PlainTextResponse)
async def render_ascii(req: ParseRequest):
    """
    Parses a sentence and returns the ASCII tree representation.
    """
    params = get_server_params(req)

    try:
        root_node = get_syntax_tree(req.text, params=params)

        if not root_node:
            raise HTTPException(status_code=422, detail=_PARSER_RETURNED_NO_TREE)

        lines = []
        for pre, _, node in RenderTree(root_node):
            label = getattr(node, "label", node.name)
            content = f": {node.word}" if hasattr(node, "word") and node.word else ""
            lines.append(f"{pre}{label}{content}")

        return "\n".join(lines)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/render/graphviz", responses={200: {"content": {"image/png": {}}}})
async def render_graphviz(req: ParseRequest):
    """
    Returns a PNG image of the syntax tree using Graphviz.
    """
    params = get_server_params(req)

    try:
        root_node = get_syntax_tree(req.text, params=params)
        if not root_node:
            raise HTTPException(status_code=422, detail=_PARSER_RETURNED_NO_TREE)

        dot_source = get_graphviz_dot(root_node)
        # Render to PNG bytes
        png_bytes = graphviz.Source(dot_source).pipe(format="png")

        return Response(content=png_bytes, media_type="image/png")

    except HTTPException:
        raise
    except graphviz.backend.ExecutableNotFound as exc:
        raise HTTPException(
            status_code=500, detail="Graphviz executable 'dot' not found on server."
        ) from exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/render/json", response_model=SyntaxNode)
async def render_json(req: ParseRequest):
    """
    Returns the raw JSON tree structure (SyntaxNode) without metadata wrappers.
    """
    params = get_server_params(req)

    try:
        root_node = get_syntax_tree(req.text, params=params)
        if not root_node:
            raise HTTPException(status_code=422, detail=_PARSER_RETURNED_NO_TREE)

        return anytree_to_pydantic(root_node)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/render/lisp", response_class=PlainTextResponse)
async def render_lisp(req: ParseRequest):
    """
    Returns the original Penn Treebank string (S-expression).
    """
    params = get_server_params(req)

    try:
        root_node = get_syntax_tree(req.text, params=params)
        if not root_node:
            raise HTTPException(status_code=422, detail=_PARSER_RETURNED_NO_TREE)

        # Retrieve raw_lisp attached by the engine
        lisp_str = getattr(root_node, "raw_lisp", None)
        if not lisp_str:
            raise HTTPException(
                status_code=404,
                detail="Original LISP string not available for this model.",
            )

        return lisp_str

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
