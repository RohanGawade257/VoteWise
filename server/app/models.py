from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Dict

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class GuidedFlowInput(BaseModel):
    """Optional guided flow state sent by the frontend. Fully backward-compatible."""
    active: bool = False
    step: Optional[str] = None        # current step name e.g. "ask_age_status"
    state: Dict[str, Any] = {}        # collected answers so far

class ConversationContextInput(BaseModel):
    """Context tracking across turns."""
    active: bool = False
    flow_type: Optional[str] = None
    last_topic: Optional[str] = None
    last_action: Optional[str] = None
    last_path_steps: List[Dict[str, Any]] = []
    current_step_index: Optional[int] = None
    awaiting_user_choice: bool = False


class ChatRequest(BaseModel):
    """
    Validated chat request.

    Security constraints:
    - message: stripped, non-empty, max 1 500 chars
    - persona: normalised to a known value; unknown values silently default to 'general'
    - context: optional, max 1 000 chars
    - guidedFlow: optional object, never a primitive
    """
    message: str = Field(..., max_length=1500, description="User question (max 1 500 chars).")
    persona: str = Field(default="general", description="Assistant tone preset.")
    context: Optional[str] = Field(default=None, max_length=1000)
    use_current_info: bool = False
    guidedFlow: Optional[GuidedFlowInput] = None
    conversationContext: Optional[ConversationContextInput] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty or whitespace only.")
        return v

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        v = v.strip().lower()
        # Alias: frontend may send 'school-student'
        if v == "school-student":
            return "student"
        allowed = {"general", "first-time-voter", "student", "elderly"}
        if v not in allowed:
            # Silently default — no 422 for unknown persona
            return "general"
        return v


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class SourceItem(BaseModel):
    title: str
    url: str
    type: str  # "official" | "rag" | "web"


class SafetyInfo(BaseModel):
    blocked: bool
    reason: Optional[str] = None


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
    
    # Conversation context meta
    conversation_context_active: bool = False
    last_topic: Optional[str] = None
    last_action: Optional[str] = None
    followup_intent: Optional[str] = None
    context_reset: bool = False
    conversation_context: Dict[str, Any] = {}
    
    # Rate-limit / error meta (used by error handlers)
    rate_limited: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    safety: SafetyInfo
    meta: MetaInfo
