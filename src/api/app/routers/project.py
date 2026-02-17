from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.grammatomy.project_engine import ProjectEngine

router = APIRouter()


class CreateProjectRequest(BaseModel):
    text: str
    name: str = "New Project"
    lang: str = "es"


class ProjectResponse(BaseModel):
    meta: Dict[str, Any]
    source_text: str
    units: list


@router.post("/create", response_model=ProjectResponse)
async def create_project(req: CreateProjectRequest):
    """
    Creates a new project from raw text.
    Performs segmentation, parsing, and fragmentation on the server side.
    """
    try:
        engine = ProjectEngine()
        project = engine.create_project(req.text, req.name, req.lang)
        return ProjectResponse(**project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
