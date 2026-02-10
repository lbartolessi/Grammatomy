"""
Main FastAPI application for the Grammatomy service.
"""

import mimetypes
import time
import traceback
from pathlib import Path

import fastapi.responses
import graphviz
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from core.grammatomy import get_syntax_tree, to_json, to_ptb
from core.grammatomy.validation_engine import ValidationEngine
from core.grammatomy.visualization.ascii_renderer import render_ascii_colored
from core.grammatomy.visualization.graphviz_renderer import get_graphviz_dot

from .schemas import ParseRequest, ParseResponse, SyntaxNode

app = FastAPI(
    title="Grammatomy API",
    description="RESTful service for constituency parsing.",
    version="0.1.0",
)

ERROR_PARSER_FAILED = "Parser returned no tree"

# Initialize Validation Engine (Singleton-ish)
RULES_PATH = Path(__file__).resolve().parents[2] / "core" / "rules_es.yaml"
validator = ValidationEngine(str(RULES_PATH), lang="es")


def _convert_to_syntax_node(node) -> SyntaxNode:
    """
    Converts an anytree Node (from core) to a Pydantic SyntaxNode (for API response).
    Extracts dynamic attributes while ignoring internal anytree fields.
    """
    attrs = {
        k: v
        for k, v in vars(node).items()
        if not k.startswith("_") and k not in ("name", "parent", "children")
    }
    return SyntaxNode(
        label=node.name,
        word=node.name if node.is_leaf else None,
        attributes=attrs,
        children=[_convert_to_syntax_node(child) for child in node.children],
    )


@app.get("/")
def read_root():
    return {"message": "Grammatomy API is running."}


@app.post("/api/parse", response_model=ParseResponse)
def parse_text(request: ParseRequest):
    """
    Analyzes text and returns a constituency tree.
    """
    start_time = time.time()

    params = {
        "engine": request.engine,
        "lang": request.lang,
        "model_package": request.model_package,
        "use_gpu": False,  # Force CPU for stability in dev
    }

    try:
        root = get_syntax_tree(request.text, params=params)
        elapsed = time.time() - start_time

        if root:
            ptb_string = to_ptb(root)
            return ParseResponse(
                root=_convert_to_syntax_node(root),
                ptb=ptb_string,
                meta={"engine": request.engine, "time": elapsed, "status": "success"},
            )
        else:
            return ParseResponse(
                root=None,
                ptb=None,
                meta={"engine": request.engine, "time": elapsed, "status": "failed"},
                error=ERROR_PARSER_FAILED,
            )

    except Exception as e:
        # Log full traceback to console for debugging
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/render/ascii")
def render_ascii(request: ParseRequest):
    params = {
        "engine": request.engine,
        "lang": request.lang,
        "model_package": request.model_package,
        "use_gpu": False,
    }
    try:
        root = get_syntax_tree(request.text, params=params)
        if not root:
            raise HTTPException(status_code=400, detail=ERROR_PARSER_FAILED)
        return fastapi.responses.PlainTextResponse(render_ascii_colored(root))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/render/json")
def render_json(request: ParseRequest):
    params = {
        "engine": request.engine,
        "lang": request.lang,
        "model_package": request.model_package,
        "use_gpu": False,
    }
    try:
        root = get_syntax_tree(request.text, params=params)
        if not root:
            raise HTTPException(status_code=400, detail=ERROR_PARSER_FAILED)
        # to_json returns a string, we parse it back to return as JSON object or return Raw
        return fastapi.responses.Response(content=to_json(root), media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/render/lisp")
def render_lisp(request: ParseRequest):
    params = {
        "engine": request.engine,
        "lang": request.lang,
        "model_package": request.model_package,
        "use_gpu": False,
    }
    try:
        root = get_syntax_tree(request.text, params=params)
        if not root:
            raise HTTPException(status_code=400, detail=ERROR_PARSER_FAILED)

        # Check for raw_lisp attribute as required by test_render_lisp_missing_attr
        raw_lisp = getattr(root, "raw_lisp", None)
        if raw_lisp:
            return fastapi.responses.PlainTextResponse(raw_lisp)

        raise HTTPException(status_code=404, detail="Original LISP string not available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/render/graphviz")
def render_graphviz(request: ParseRequest):
    params = {
        "engine": request.engine,
        "lang": request.lang,
        "model_package": request.model_package,
        "use_gpu": False,
    }
    try:
        root = get_syntax_tree(request.text, params=params)
        if not root:
            raise HTTPException(status_code=400, detail=ERROR_PARSER_FAILED)

        dot_code = get_graphviz_dot(root)

        src = graphviz.Source(dot_code)
        png_data = src.pipe(format="png")
        return fastapi.responses.Response(content=png_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Validation Endpoints ---


@app.post("/api/validation/options")
def get_validation_options(payload: dict):
    """
    Checks context compatibility and returns valid options + trace.
    Payload: { parent_tag, current_tag, children_tags }
    """
    parent = payload.get("parent_tag")
    tag = payload.get("current_tag") or ""

    # 1. Validate Context
    if parent:
        is_valid, reason = validator.can_add_child(parent, tag)
        trace = [reason]
        # 2. Get Valid Options (for dropdown)
        valid_options = sorted(list(validator.allowed_children.get(parent, [])))
    else:
        # Root context check
        is_valid = tag in validator.root_allowed_tags
        trace = ["Root check"] if is_valid else [f"'{tag}' not allowed as Root"]
        valid_options = sorted(list(validator.root_allowed_tags))

    # Fallback if no options found (e.g. terminal or unknown parent)
    if not valid_options and not parent:
        valid_options = ["S", "ROOT"]

    return {"valid": is_valid, "trace": trace, "options": sorted(valid_options)}


@app.post("/api/validation/check/requirements")
def check_requirements(payload: dict):
    """
    Checks internal structure (mandatory children).
    Payload: { tag, descendant_tags, strategy }
    """
    tag = payload.get("tag") or ""
    children = payload.get("children_tags", [])
    descendants = payload.get("descendant_tags", [])
    strategy = payload.get("strategy", "lax")

    # Fallback for backward compatibility or if children not provided
    if "children_tags" not in payload:
        children = descendants

    is_valid, errors, trace = validator.validate_node(
        node_label=tag, children_labels=children, descendants_labels=descendants, strategy=strategy
    )

    return {"allowed": is_valid, "reason": errors[0] if errors else "", "trace": trace}


# --- Static File Serving (Production) ---
# Serve the built frontend if the 'dist/web' directory exists.
# This allows the API and Frontend to run in a single container (e.g. HF Spaces).
DIST_DIR = Path(__file__).resolve().parents[3] / "dist" / "web"

if DIST_DIR.exists():
    # Ensure MIME types for fonts are registered (critical for Slim images)
    mimetypes.add_type("font/woff2", ".woff2")
    mimetypes.add_type("font/ttf", ".ttf")

    # Debug: Verify build integrity on startup
    print(f"📂 Static Root: {DIST_DIR}")
    fonts_dir = DIST_DIR / "fonts"
    if fonts_dir.exists():
        print(f"   ✅ Fonts detected: {[f.name for f in fonts_dir.iterdir()]}")
    else:
        print(f"   ⚠️ WARNING: 'fonts' directory missing in {DIST_DIR}")

    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
else:
    print(f"Notice: Frontend build not found at {DIST_DIR}. Running API only.")
