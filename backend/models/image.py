from beanie import Document
from pydantic import Field, ConfigDict
from utils.pydantic_objectid import PyObjectId
from typing import Optional

class Image(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    pdf_id: PyObjectId = Field(index=True)
    page_number: int = Field(index=True)
    cloudinary_url: str
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "images"
