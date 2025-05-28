from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime
from utils.pydantic_objectid import PyObjectId
from typing import Optional

class ChatSession(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(index=True)
    pdf_id: PyObjectId = Field(index=True)
    
    # Session info
    title: str = "New Chat"
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "chat_sessions"
