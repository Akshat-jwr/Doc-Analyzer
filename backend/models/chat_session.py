from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    pdf_id: int = Field(foreign_key="pdfs.id", index=True)
    
    # Session info
    title: str = Field(max_length=200, default="New Chat")
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="chat_sessions")
    pdf: Optional["PDF"] = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session", cascade_delete=True)
