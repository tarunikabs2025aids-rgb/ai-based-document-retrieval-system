from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentMetadataResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_hash: str
    chunk_count: int
    indexed_at: datetime

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_chats: int
    total_messages: int
    average_confidence: float
    feedback_ratio: float # Positive vs Negative feedback percentage
    language_distribution: Dict[str, int]
    popular_schemes: List[Dict[str, Any]]
    popular_states: List[Dict[str, Any]]

class VectorDbStatus(BaseModel):
    is_indexed: bool
    pdf_count: int
    csv_count: int
    total_vectors: int
    last_indexed: Optional[datetime] = None
