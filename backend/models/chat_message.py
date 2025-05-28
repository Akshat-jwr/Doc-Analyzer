from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime
from enum import Enum
from utils.pydantic_objectid import PyObjectId
from typing import Optional

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    session_id: PyObjectId = Field(index=True)
    
    # Essential message data
    content: str
    message_type: MessageType = Field(index=True)
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "chat_messages"
