from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PDF(SQLModel, table=True):
    __tablename__ = "pdfs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Essential file info
    filename: str = Field(max_length=500)
    cloudinary_url: str = Field(max_length=1000)
    page_count: int = Field(default=0)
    
    # Processing
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.UPLOADED)
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="pdfs")
    page_texts: List["PageText"] = Relationship(back_populates="pdf", cascade_delete=True)
    tables: List["Table"] = Relationship(back_populates="pdf", cascade_delete=True)
    images: List["Image"] = Relationship(back_populates="pdf", cascade_delete=True)
    chat_sessions: List["ChatSession"] = Relationship(back_populates="pdf")
