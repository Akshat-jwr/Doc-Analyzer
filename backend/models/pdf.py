from beanie import Document
from pydantic import Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
from utils.pydantic_objectid import PyObjectId

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TEXT_IMAGES_COMPLETE = "text_images_complete"  # Phase 1 done - ready for general queries
    BACKGROUND_PROCESSING = "background_processing"  # Table extraction running in background
    COMPLETED = "completed"  # Everything done - analytics ready
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
    
    # Background processing info
    tables_processed: int = 0  # Track progress
    total_tables_found: int = 0  # Total tables discovered
    background_error: Optional[str] = None  # Track background errors
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    text_images_completed_at: Optional[datetime] = None
    fully_completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "pdfs"
