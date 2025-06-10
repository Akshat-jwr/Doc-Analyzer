from beanie import Document
from pydantic import Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentChunk(Document):
    """Document chunk model for vector storage"""
    document_id: str = Field(index=True)
    page_number: int = Field(index=True)
    chunk_index: int
    content_type: str = Field(index=True)  # 'text', 'image', 'table'
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    similarity: Optional[float] = None  # ✅ ADD THIS FIELD
    
    class Settings:
        collection = "document_chunks"
        indexes = [
            [("document_id", 1), ("content_type", 1)],
            [("document_id", 1), ("page_number", 1)],
        ]
