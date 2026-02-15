from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SyntaxNode(BaseModel):
    """
    Recursive definition of a Constituency Tree Node.
    """

    label: str = Field(..., description="Syntactic category (e.g., NP, VP) or POS tag")
    word: Optional[str] = Field(None, description="Terminal word (leaf nodes only)")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Morphological features or metadata"
    )
    children: List["SyntaxNode"] = Field(default_factory=list, description="Child nodes")

    # Required for recursive models in Pydantic V2
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


# Update forward reference for recursion
SyntaxNode.model_rebuild()


class ParseRequest(BaseModel):
    text: str = Field(
        ...,
        json_schema_extra={"example": "El veloz murciélago hindú comía feliz cardillo y kiwi."},
    )
    engine: str = Field("stanza", pattern="^(stanza|spacy)$")
    lang: str = Field("es", min_length=2, max_length=2)
    model_package: str = "default"


class ParseResponse(BaseModel):
    root: Optional[SyntaxNode]
    ptb: Optional[str] = Field(None, description="Penn Treebank S-expression string")
    meta: Dict[str, Any] = Field(..., description="Execution metadata (time, engine used)")
    error: Optional[str] = None


class TagOptionsRequest(BaseModel):
    parent_tag: Optional[str] = None
    current_tag: str
    children_tags: List[str] = []


class RenderRequest(BaseModel):
    ptb: str
    format: str = Field("png", description="Output format: png, svg, webp, ascii, latex")
