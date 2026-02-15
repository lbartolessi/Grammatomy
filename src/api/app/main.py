"""
Main FastAPI application for the Grammatomy service.
"""

import mimetypes
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List

import fastapi.responses
import graphviz
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.grammatomy import get_syntax_tree, to_json, to_latex, to_ptb
from core.grammatomy.fragmentation import FragmentationEngine
from core.grammatomy.grammar import GRAMMAR_RULES, NODE_DESCRIPTIONS
from core.grammatomy.parsers.lisp_parser import LispParser
from core.grammatomy.validation_engine import ValidationEngine
from core.grammatomy.visualization.ascii_renderer import render_ascii_colored
from core.grammatomy.visualization.graphviz_renderer import get_graphviz_dot

from .schemas import ParseRequest, ParseResponse, RenderRequest, SyntaxNode
from .routers import mutation

app = FastAPI(
    title="Grammatomy API",
    description="RESTful service for constituency parsing.",
    version="0.1.0",
)

app.include_router(mutation.router, prefix="/api/mutation", tags=["Mutation"])

ERROR_PARSER_FAILED = "Parser returned no tree"

# Initialize Validation Engine (Singleton-ish)
# Unify rule loading to use the same source as the core components.
# This prevents inconsistencies between API validation and internal logic.
RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "grammatomy"
    / "assets"
    / "rules"
    / "hybrid_rules.yaml"
)
validator = ValidationEngine(str(RULES_PATH), lang="es")

# Initialize Fragmentation Engine
fragmentation_engine = FragmentationEngine()

# Initialize Lisp Parser for exports
lisp_parser = LispParser()


# Request Models for Fragmentation Tools
class FragmentRequest(BaseModel):
    ptb: str


class DefragmentRequest(BaseModel):
    main_ptb: str
    subtrees: List[Dict[str, Any]]


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


@app.get("/api/validation/tags")
def get_validation_tags():
    """
    Returns the inventory of tags and grammar rules for the UI.
    This allows the frontend to show tooltips and validate structure.
    """
    return {"rules": GRAMMAR_RULES, "descriptions": NODE_DESCRIPTIONS}


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


@app.get("/api/validation/rules/{tag}")
def get_validation_rule(tag: str):
    """
    Returns the rule definition for a specific tag.
    """
    # Direct lookup to avoid warning logs in ValidationEngine for leaf words
    if tag in validator.rules:
        return validator.rules[tag]

    # Return empty object for unknown tags (words) to avoid 404 errors in logs
    return {}


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


# --- Export Endpoints ---


@app.post("/api/export/image")
def export_image(request: RenderRequest):
    try:
        # Parse PTB to AnyTree
        root = lisp_parser.to_anytree(request.ptb)
        if not root:
            raise HTTPException(status_code=400, detail="Invalid PTB string")

        # Generate DOT and Render
        dot_code = get_graphviz_dot(root)
        src = graphviz.Source(dot_code)
        data = src.pipe(format=request.format)

        media_type = "image/png"
        if request.format == "svg":
            media_type = "image/svg+xml"
        elif request.format == "webp":
            media_type = "image/webp"

        return fastapi.responses.Response(content=data, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/export/ascii")
def export_ascii(request: RenderRequest):
    try:
        # Parse PTB to AnyTree
        root = lisp_parser.to_anytree(request.ptb)
        if not root:
            raise HTTPException(status_code=400, detail="Invalid PTB string")

        # Render ASCII (using the colored renderer but returning plain text response)
        return fastapi.responses.PlainTextResponse(render_ascii_colored(root))
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/export/latex")
def export_latex(request: RenderRequest):
    try:
        # Parse PTB to AnyTree
        root = lisp_parser.to_anytree(request.ptb)
        if not root:
            raise HTTPException(status_code=400, detail="Invalid PTB string")

        # Render LaTeX Forest
        return fastapi.responses.PlainTextResponse(to_latex(root))
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Fragmentation Tools Endpoints ---


@app.post("/api/tools/fragment")
def fragment_tree(request: FragmentRequest):
    try:
        main_ptb, subtrees = fragmentation_engine.fragment(request.ptb)
        return {"main_ptb": main_ptb, "subtrees": subtrees}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/tools/defragment")
def defragment_tree(request: DefragmentRequest):
    try:
        ptb = fragmentation_engine.defragment(request.main_ptb, request.subtrees)
        return {"ptb": ptb}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/export/ascii")
def export_ascii(request: RenderRequest):
    try:
        # Parse PTB to AnyTree
        root = lisp_parser.to_anytree(request.ptb)
        if not root:
            raise HTTPException(status_code=400, detail="Invalid PTB string")

        # Render ASCII (using the colored renderer but returning plain text response)
        return fastapi.responses.PlainTextResponse(render_ascii_colored(root))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


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
