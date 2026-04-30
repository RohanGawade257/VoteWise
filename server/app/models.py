from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class GuidedFlowInput(BaseModel):
    """Optional guided flow state sent by the frontend. Fully backward-compatible."""
    active: bool = False
    step: Optional[str] = None        # current step name e.g. "ask_age_status"
    state: Dict[str, Any] = {}        # collected answers so far

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    persona: str = Field(default="general", pattern="^(general|first-time-voter|student|elderly)$")
    context: Optional[str] = Field(default=None, max_length=500)
    use_current_info: bool = False
    guidedFlow: Optional[GuidedFlowInput] = None   # NEW — optional, backward-compatible

# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

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
    contextual_followup_intent: Optional[str] = None
    used_direct_answer: bool = False
    used_model: bool = False
    persona_used: str = "general"
    rag_confidence: str = "none"          # high | medium | low | none
    rag_chunks_used: int = 0
    source_files_used: List[str] = []
    checkedAt: Optional[str] = None
    sourceType: Optional[str] = None
    used_rag_fallback: bool = False
    fallback_reason: Optional[str] = None
    # Guided flow meta — all optional so existing responses are unaffected
    guided_flow_active: bool = False
    guided_flow_step: Optional[str] = None
    guided_flow_state: Dict[str, Any] = {}
    suggested_replies: List[str] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    safety: SafetyInfo
    meta: MetaInfo
