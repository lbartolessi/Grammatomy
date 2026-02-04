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

from grammatomy import get_syntax_tree, to_ptb
from grammatomy.validation import METASYNTAX_RULES

from .schemas import ParseRequest, ParseResponse

app = FastAPI(
    title="Grammatomy API",
    description="RESTful service for constituency parsing.",
    version="0.1.0",
)


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

        ptb_string = to_ptb(root) if root else None

        return ParseResponse(
            root=root,  # Pydantic will serialize the AnyTree node recursively
            ptb=ptb_string,
            meta={"engine": request.engine, "time": elapsed},
        )
    except Exception as e:
        # Log full traceback to console for debugging
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules")
def get_validation_rules():
    """
    Returns the active metasyntactic rules for the frontend editor.
    """
    return METASYNTAX_RULES


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
