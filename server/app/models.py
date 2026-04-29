from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    persona: str = Field(default="general", pattern="^(general|first-time-voter|student|elderly)$")
    context: Optional[str] = Field(default=None, max_length=500)
    use_current_info: bool = False

class SourceItem(BaseModel):
    title: str
    url: str
    type: str  # "official" | "rag" | "web"

class SafetyInfo(BaseModel):
    blocked: bool
    reason: Optional[str]

class MetaInfo(BaseModel):
    model: str
    used_rag: bool
    used_search_grounding: bool
    intent: str = "unknown"
    used_direct_answer: bool = False
    used_model: bool = False
    checkedAt: Optional[str] = None
    sourceType: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    safety: SafetyInfo
    meta: MetaInfo
