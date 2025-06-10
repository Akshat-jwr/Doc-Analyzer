from beanie import Document
from pydantic import Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from utils.pydantic_objectid import PyObjectId
from enum import Enum

class ChatType(str, Enum):
    GENERAL = "general"
    ANALYTICAL = "analytical" 
    VISUALIZATION = "visualization"

class ChatMessage(Document):
    """Enhanced chat message with multi-chat support"""
    session_id: str = Field(index=True)
    user_id: PyObjectId = Field(index=True)
    document_id: Optional[PyObjectId] = Field(index=True, default=None)
    chat_type: ChatType = Field(index=True)
    role: str  # 'user' or 'assistant'
    content: str
    images_analyzed: List[str] = []  # URLs of images analyzed in this message
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        collection = "chat_messages"
        indexes = [
            [("session_id", 1), ("timestamp", 1)],
            [("user_id", 1), ("chat_type", 1), ("timestamp", -1)],
            [("document_id", 1), ("chat_type", 1), ("timestamp", -1)]
        ]

class ChatSession(Document):
    """Enhanced chat session with multi-chat support"""
    session_id: str = Field(index=True, unique=True)
    user_id: PyObjectId = Field(index=True)
    document_id: Optional[PyObjectId] = Field(index=True, default=None)
    chat_type: ChatType = Field(index=True)
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    message_count: int = 0
    is_active: bool = True
    last_activity: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        collection = "chat_sessions"
        indexes = [
            [("user_id", 1), ("chat_type", 1), ("updated_at", -1)],
            [("document_id", 1), ("chat_type", 1), ("updated_at", -1)],
            [("session_id", 1), ("chat_type", 1)]
        ]
