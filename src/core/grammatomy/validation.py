"""
API Router para Validación Gramatical.

Este módulo expone los endpoints REST relacionados con la validación de
estructuras, verificación de movimientos y consulta de reglas. Actúa como
interfaz HTTP sobre el `ValidationEngine`.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.grammatomy.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])

#: Ruta absoluta al archivo de reglas híbridas.
RULES_PATH = Path(__file__).parent / "assets" / "rules" / "hybrid_rules.yaml"


def get_engine(lang: str = "es") -> ValidationEngine:
    """
    Helper para obtener la instancia singleton del motor de validación.
    """
    try:
        return ValidationEngine(str(RULES_PATH), lang)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load validation engine: {str(e)}"
        ) from e


class TagOptionsRequest(BaseModel):
    """Esquema para solicitar opciones de etiquetado válidas."""

    parent_tag: Optional[str] = None
    current_tag: str
    children_tags: List[str] = []


class MoveCheckRequest(BaseModel):
    """Esquema para verificar movimiento de nodos."""

    parent_tag: str
    child_tag: str
    lang: str = "es"


class DeleteCheckRequest(BaseModel):
    """Esquema para verificar borrado de nodos."""

    parent_tag: str
    child_tag: str
    sibling_tags: List[str]
    lang: str = "es"


class ConversionCheckRequest(BaseModel):
    """Esquema para verificar conversión de etiquetas."""

    current_tag: str
    ancestor_tags: List[str]
    children_tags: List[str]
    lang: str = "es"


class RequirementsCheckRequest(BaseModel):
    """Esquema para verificar requisitos internos (hijos obligatorios)."""

    tag: str
    descendant_tags: List[str]
    children_tags: List[str] = []
    lang: str = "es"


class ValidationResponse(BaseModel):
    """Respuesta estándar de validación."""

    allowed: bool
    reason: str


@router.get("/tags", response_model=List[str])
def get_all_tags(lang: str = "es"):
    """Retorna una lista ordenada de todas las etiquetas válidas."""
    engine = get_engine(lang)
    return engine.get_all_tags()


@router.get("/rules/{tag}", response_model=Dict[str, Any])
def get_tag_definition(tag: str, lang: str = "es"):
    """Retorna la definición cruda de una etiqueta (para inspección en UI)."""
    logger.info("API Request: get_tag_definition for tag='%s'", tag)
    engine = get_engine(lang)
    result = engine.get_definition(tag)
    logger.debug(
        "Result found: %s (Keys: %s)", bool(result), list(result.keys()) if result else "None"
    )
    return result


@router.post("/check/move", response_model=ValidationResponse)
def validate_move(req: MoveCheckRequest):
    """
    Valida si un nodo hijo puede ser movido bajo un nodo padre.
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.can_add_child(req.parent_tag, req.child_tag)
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/check/conversion", response_model=List[str])
def get_valid_conversions(req: ConversionCheckRequest):
    """
    Retorna etiquetas válidas a las que se puede convertir el nodo actual.
    """
    engine = get_engine(req.lang)
    return engine.can_convert_node(req.ancestor_tags, req.children_tags)


@router.post("/check/requirements", response_model=ValidationResponse)
def validate_requirements(req: RequirementsCheckRequest):
    """
    Valida si un nodo satisface sus requisitos internos obligatorios.
    """
    engine = get_engine(req.lang)
    is_valid, errors, _ = engine.validate_node(
        node_label=req.tag,
        children_labels=req.children_tags,  # Strict mode uses immediate children
        strategy="strict",
    )
    allowed = is_valid
    reason = errors[0] if errors else "OK"
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/check/delete", response_model=ValidationResponse)
def validate_delete(req: DeleteCheckRequest):
    """
    Valida si un nodo puede ser borrado sin violar restricciones del padre.
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.can_delete_child(req.parent_tag, req.child_tag, req.sibling_tags)
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/check/add_child", response_model=ValidationResponse)
def validate_add_child(req: MoveCheckRequest):
    """
    Valida si un padre puede aceptar un tipo específico de hijo.
    """
    engine = get_engine(req.lang)
    allowed, reason = engine.can_add_child(req.parent_tag, req.child_tag)
    return ValidationResponse(allowed=allowed, reason=reason)


@router.post("/options", response_model=List[str])
def get_tag_options(payload: TagOptionsRequest):
    """
    Devuelve las etiquetas válidas para un nodo dado su contexto (padre e hijos).
    """
    engine = get_engine()  # Assumes default lang 'es' for now
    return engine.get_valid_substitutions(
        parent=payload.parent_tag,
        children=payload.children_tags,
    )
