from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Table(SQLModel, table=True):
    __tablename__ = "tables"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pdf_id: int = Field(foreign_key="pdfs.id", index=True)
    
    # Page range for multi-page tables
    start_page: int = Field(index=True)
    end_page: int = Field(index=True)
    table_number: int  # Table number within the document
    
    # Content (MD format only)
    table_title: Optional[str] = Field(max_length=500)
    markdown_content: str  # Complete table in markdown format
    
    # Structure metadata
    column_count: int
    row_count: int
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    pdf: Optional["PDF"] = Relationship(back_populates="tables")
