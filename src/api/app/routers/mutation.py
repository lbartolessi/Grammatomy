from typing import Any, Dict, List, Optional

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
    node_path: List[int]
    fragment_label: str
    parent_context_label: str
    target_label: Optional[str] = None


class DetachResponse(BaseModel):
    main_ptb: str
    fragment_ptb: str
    integrity_check: Optional[Dict[str, Any]] = None


class DeleteRequest(BaseModel):
    main_ptb: str
    node_index: int


class DeleteResponse(BaseModel):
    ptb: str


@router.post("/reabsorb", response_model=ReabsorbResponse)
async def reabsorb_subtree(req: ReabsorbRequest):
    try:
        print(
            f"[reabsorb] link_label='{req.link_label}' "
            f"main_ptb_len={len(req.main_ptb)} "
            f"fragment_ptb_len={len(req.fragment_ptb)}"
        )
        # Delegate to Core Logic
        result = MutationEngine.reabsorb(req.main_ptb, req.fragment_ptb, req.link_label)
        print(f"[reabsorb] SUCCESS: link_label='{req.link_label}'")
        return ReabsorbResponse(**result)
    except ValueError as ve:
        print(f"[reabsorb] FAILED (ValueError): {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        print(f"[reabsorb] FAILED (Exception): {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/detach", response_model=DetachResponse)
async def detach_subtree(req: DetachRequest):
    try:
        print(f"[detach] fragment_label='{req.fragment_label}' node_path={req.node_path}")
        result = MutationEngine.detach(
            req.main_ptb,
            req.node_path,
            req.fragment_label,
            req.parent_context_label,
            req.target_label,
        )
        print(f"[detach] SUCCESS: fragment_label='{req.fragment_label}'")
        return DetachResponse(**result)
    except ValueError as ve:
        print(f"[detach] FAILED (ValueError): {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        print(f"[detach] FAILED (Exception): {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/delete", response_model=DeleteResponse)
async def delete_node(req: DeleteRequest):
    try:
        result = MutationEngine.delete_node(req.main_ptb, req.node_index)
        return DeleteResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
