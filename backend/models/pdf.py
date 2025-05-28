from beanie import Document
from pydantic import Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
from utils.pydantic_objectid import PyObjectId

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PDF(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(index=True)
    
    # Essential file info
    filename: str
    cloudinary_url: str
    page_count: int = 0
    
    # Processing
    processing_status: ProcessingStatus = ProcessingStatus.UPLOADED
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "pdfs"
