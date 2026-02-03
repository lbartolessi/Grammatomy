from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class SyntaxNode(BaseModel):
    """
    Recursive definition of a Constituency Tree Node.
    """
    label: str = Field(..., description="Syntactic category (e.g., NP, VP) or POS tag")
    word: Optional[str] = Field(None, description="Terminal word (leaf nodes only)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Morphological features or metadata")
    children: List['SyntaxNode'] = Field(default_factory=list, description="Child nodes")

    # Required for recursive models in Pydantic V2
    model_config = ConfigDict(populate_by_name=True)

# Update forward reference for recursion
SyntaxNode.model_rebuild()

class ParseRequest(BaseModel):
    text: str = Field(..., json_schema_extra={"example": "El veloz murciélago hindú comía feliz cardillo y kiwi."})
    engine: str = Field("stanza", pattern="^(stanza|spacy)$")
    lang: str = Field("es", min_length=2, max_length=2)
    model_package: str = "default"

class ParseResponse(BaseModel):
    root: Optional[SyntaxNode]
    meta: Dict[str, Any] = Field(..., description="Execution metadata (time, engine used)")
    error: Optional[str] = None