from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.grammatomy.mutation import MutationEngine

router = APIRouter()


class ReabsorbRequest(BaseModel):
    main_ptb: str
    fragment_ptb: str
    link_label: str


class ReabsorbResponse(BaseModel):
    ptb: str
    focus_index: int = -1


class DetachRequest(BaseModel):
    main_ptb: str
    node_index: int
    fragment_label: str
    parent_context_label: str


class DetachResponse(BaseModel):
    main_ptb: str
    fragment_ptb: str


@router.post("/reabsorb", response_model=ReabsorbResponse)
async def reabsorb_subtree(req: ReabsorbRequest):
    try:
        # Delegate to Core Logic
        result = MutationEngine.reabsorb(req.main_ptb, req.fragment_ptb, req.link_label)
        return ReabsorbResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detach", response_model=DetachResponse)
async def detach_subtree(req: DetachRequest):
    try:
        result = MutationEngine.detach(
            req.main_ptb, req.node_index, req.fragment_label, req.parent_context_label
        )
        return DetachResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
