from beanie import Document
from pydantic import Field, ConfigDict
from typing import Optional
from datetime import datetime
from utils.pydantic_objectid import PyObjectId

class Table(Document):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    pdf_id: PyObjectId = Field(index=True)
    
    # Page range for multi-page tables
    start_page: int = Field(index=True)
    end_page: int = Field(index=True)
    table_number: int
    
    # Content (MD format only)
    table_title: Optional[str] = None
    markdown_content: str
    
    # Structure metadata
    column_count: int
    row_count: int
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str}
    )
    
    class Settings:
        collection = "tables"
