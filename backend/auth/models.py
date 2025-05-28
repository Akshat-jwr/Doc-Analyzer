from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime
from utils.pydantic_objectid import PyObjectId
from typing import Optional

class OTP(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: str = Field(index=True)
    otp_code: str
    expires_at: datetime
    is_used: bool = False
    purpose: str = "login"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "otps"
