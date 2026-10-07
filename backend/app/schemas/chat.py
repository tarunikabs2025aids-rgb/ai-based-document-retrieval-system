from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class Citation(BaseModel):
    source: str         # Document/Dataset name
    page: Optional[int] = None
    chunk: str          # Exact text snippet
    official_website: Optional[str] = None
    confidence: float   # Search score match percentage
    row_index: Optional[int] = None # For CSV row index

class ActionTimelineItem(BaseModel):
    step: int
    title: str
    description: str
    timeline: str # e.g. "Within 3 days"
    status: str # "pending" | "completed" | "current"

class ActionPlan(BaseModel):
    required_documents: List[str]
    application_form_url: Optional[str] = None
    where_to_apply: str
    office_address: Optional[str] = None
    processing_time: str
    application_fees: str
    checklist: List[str]
    timeline: List[ActionTimelineItem]
    warnings: List[str]
    notes: List[str]

class ChatInput(BaseModel):
    message: str
    conversation_id: Optional[str] = None # Generate on client if None
    language: Optional[str] = None # Auto-detect if None

class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    original_content: Optional[str] = None
    language: str
    citations: Optional[List[Citation]] = None
    action_plan: Optional[ActionPlan] = None
    confidence: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    title: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class FeedbackInput(BaseModel):
    message_id: int
    rating: int # 1 or -1
    comment: Optional[str] = None
