from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None

class SourceDocument(BaseModel):
    content: str
    metadata: dict
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    confidence: float
    filtered: bool
