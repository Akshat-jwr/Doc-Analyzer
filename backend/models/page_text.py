from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class PageText(SQLModel, table=True):
    __tablename__ = "page_texts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pdf_id: int = Field(foreign_key="pdfs.id", index=True)
    page_number: int = Field(index=True)
    extracted_text: str
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    pdf: Optional["PDF"] = Relationship(back_populates="page_texts")
