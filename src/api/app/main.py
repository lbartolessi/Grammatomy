"""
Main FastAPI application for the Grammatomy service.
"""

import mimetypes
import os
import sys
import time
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

# Import Core Logic
# Ensure src/core is in PYTHONPATH or installed in editable mode
# src/api/app/main.py -> parents[2] = src
sys.path.append(str(Path(__file__).resolve().parents[2] / "core"))

from grammatomy import get_syntax_tree, to_json, to_ptb
from grammatomy.visualization.ascii_renderer import render_ascii_colored
from grammatomy.visualization.graphviz_renderer import get_graphviz_dot
from validation_engine import ValidationEngine

from .schemas import ParseRequest, ParseResponse

app = FastAPI(
    title="Grammatomy API",
    description="RESTful service for constituency parsing.",
    version="0.1.0",
)

# Initialize Validation Engine (Singleton-ish)
RULES_PATH = Path(__file__).resolve().parents[2] / "core" / "rules_es.yaml"
validator = ValidationEngine(str(RULES_PATH), strategy="lax")


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
                root=root,
                ptb=ptb_string,
                meta={"engine": request.engine, "time": elapsed, "status": "success"},
            )
        else:
            return ParseResponse(
                root=None,
                meta={"engine": request.engine, "time": elapsed, "status": "failed"},
                error="Parser returned no tree",
            )

    except Exception as e:
        # Log full traceback to console for debugging
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
            raise HTTPException(status_code=400, detail="Parser returned no tree")
        return fastapi.responses.PlainTextResponse(render_ascii_colored(root))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            raise HTTPException(status_code=400, detail="Parser returned no tree")
        # to_json returns a string, we parse it back to return as JSON object or return Raw
        return fastapi.responses.Response(
            content=to_json(root), media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            raise HTTPException(status_code=400, detail="Parser returned no tree")

        # Check for raw_lisp attribute as required by test_render_lisp_missing_attr
        if hasattr(root, "raw_lisp") and root.raw_lisp:
            return fastapi.responses.PlainTextResponse(root.raw_lisp)

        raise HTTPException(
            status_code=404, detail="Original LISP string not available"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            raise HTTPException(status_code=400, detail="Parser returned no tree")

        dot_code = get_graphviz_dot(root)
        import graphviz

        src = graphviz.Source(dot_code)
        png_data = src.pipe(format="png")
        return fastapi.responses.Response(content=png_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Validation Endpoints ---


@app.post("/api/validation/options")
def get_validation_options(payload: dict):
    """
    Checks context compatibility and returns valid options + trace.
    Payload: { parent_tag, current_tag, children_tags }
    """
    parent = payload.get("parent_tag")
    tag = payload.get("current_tag")

    # 1. Validate Context
    is_valid, trace = validator.validate_context(tag, parent)

    # 2. Get Valid Options (for dropdown)
    # If parent is defined, what can go there?
    valid_options = []
    if parent:
        valid_options = validator._get_children_config(
            parent, validator.strategy, "allowed_children"
        )
    else:
        valid_options = ["S", "ROOT"]  # Root context

    return {"valid": is_valid, "trace": trace, "options": sorted(list(valid_options))}


@app.post("/api/validation/check/requirements")
def check_requirements(payload: dict):
    """
    Checks internal structure (mandatory children).
    Payload: { tag, descendant_tags, strategy }
    """
    tag = payload.get("tag")
    children = payload.get("children_tags", [])
    descendants = payload.get("descendant_tags", [])
    strategy = payload.get("strategy", "lax")

    # Fallback for backward compatibility or if children not provided
    if "children_tags" not in payload:
        children = descendants

    validator.set_strategy(strategy)
    is_valid, errors, trace = validator.validate_node(
        node_label=tag,
        children_labels=children,
        descendants_labels=descendants,
    )

    return {"allowed": is_valid, "reason": errors[0] if errors else "", "trace": trace}


import fastapi.responses

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
