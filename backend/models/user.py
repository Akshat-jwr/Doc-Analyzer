from beanie import Document
from pydantic import Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from utils.pydantic_objectid import PyObjectId

class User(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    full_name: str
    
    # Google Auth fields
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    profile_picture_url: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "users"
