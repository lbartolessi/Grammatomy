from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.grammatomy.fragmentation import FragmentationEngine

router = APIRouter()


class FragmentRequest(BaseModel):
    ptb: str


class SubTree(BaseModel):
    id: str
    label: str
    root_node_id: str
    ptb: str
    notes: Optional[str] = None


class FragmentResponse(BaseModel):
    main_ptb: str
    subtrees: List[SubTree]
    integrity_check: Optional[Dict[str, Any]] = None


@router.post("/fragment", response_model=FragmentResponse)
async def fragment_tree(req: FragmentRequest):
    try:
        engine = FragmentationEngine()
        main_ptb, subtrees, integrity = engine.fragment(req.ptb)
        # Convert dicts to SubTree models explicitly to satisfy type checker
        # although Pydantic does this automatically at runtime.
        subtree_models = [SubTree(**st) for st in subtrees]
        return FragmentResponse(
            main_ptb=main_ptb, subtrees=subtree_models, integrity_check=integrity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
