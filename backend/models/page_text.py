from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime
from utils.pydantic_objectid import PyObjectId
from typing import Optional

class PageText(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    pdf_id: PyObjectId = Field(index=True)
    page_number: int = Field(index=True)
    extracted_text: str
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "page_texts"
