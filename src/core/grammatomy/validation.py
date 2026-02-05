from pathlib import Path
from typing import Any, Dict, List

import grammatomy
from fastapi import APIRouter, Body, HTTPException
from grammatomy.validation_engine import ValidationEngine
from pydantic import BaseModel

router = APIRouter(prefix="/validation", tags=["validation"])

# Resolve rules path relative to the core package
RULES_PATH = Path(grammatomy.__file__).parent / "assets" / "rules" / "hybrid_rules.yaml"


def get_engine(lang: str = "es") -> ValidationEngine:
    """Dependency/Helper to get the singleton engine instance."""
    try:
        return ValidationEngine(str(RULES_PATH), lang)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load validation engine: {str(e)}"
        )


class MoveCheckRequest(BaseModel):
    parent_tag: str
    child_tag: str
    lang: str = "es"


class DeleteCheckRequest(BaseModel):
    parent_tag: str
    child_tag: str
    sibling_tags: List[str]
    lang: str = "es"


class ConversionCheckRequest(BaseModel):
    current_tag: str
    ancestor_tags: List[str]
    children_tags: List[str]
    lang: str = "es"


class RequirementsCheckRequest(BaseModel):
    tag: str
    descendant_tags: List[str]
    lang: str = "es"


class ValidationResponse(BaseModel):
    allowed: bool
    reason: str


@router.get("/tags", response_model=List[str])
def get_all_tags(lang: str = "es"):
    """Returns a sorted list of all valid tags for the dropdown."""
    engine = get_engine(lang)
    return engine.get_all_tags()


@router.get("/rules/{tag}", response_model=Dict[str, Any])
def get_tag_definition(tag: str, lang: str = "es"):
    """Returns the raw rule definition for a specific tag (for UI inspection)."""
    print(f"🔍 API Request: get_tag_definition for tag='{tag}'")
    engine = get_engine(lang)
    result = engine.get_definition(tag)
    print(
        f"   Result found: {bool(result)} (Keys: {list(result.keys()) if result else 'None'})"
    )
    return result


@router.post("/check/move", response_model=ValidationResponse)
def validate_move(req: MoveCheckRequest):
    """
    Validates if a child node can be moved under a parent node.
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.can_add_child(req.parent_tag, req.child_tag)
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/check/conversion", response_model=List[str])
def get_valid_conversions(req: ConversionCheckRequest):
    """
    Returns a list of valid tags that the current node can be converted to,
    based on its parent and children constraints.
    """
    engine = get_engine(req.lang)
    return engine.can_convert_node(
        req.current_tag, req.ancestor_tags, req.children_tags
    )


@router.post("/check/requirements", response_model=ValidationResponse)
def validate_requirements(req: RequirementsCheckRequest):
    """
    Validates if a node satisfies its internal mandatory requirements (based on descendants).
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.validate_requirements(req.tag, req.descendant_tags)
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/check/delete", response_model=ValidationResponse)
def validate_delete(req: DeleteCheckRequest):
    """
    Validates if a node can be deleted without violating mandatory child constraints of its parent.
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.can_delete_child(
        req.parent_tag, req.child_tag, req.sibling_tags
    )
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/check/add_child", response_model=ValidationResponse)
def validate_add_child(req: MoveCheckRequest):
    """
    Validates if a parent can accept a specific type of child.
    Reuses MoveCheckRequest structure as arguments are identical.
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.can_add_child(req.parent_tag, req.child_tag)
    return ValidationResponse(allowed=allowed, reason=reason)
