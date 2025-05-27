from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class Image(SQLModel, table=True):
    __tablename__ = "images"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pdf_id: int = Field(foreign_key="pdfs.id", index=True)
    page_number: int = Field(index=True)
    cloudinary_url: str = Field(max_length=1000)
    
    # Relationships
    pdf: Optional["PDF"] = Relationship(back_populates="images")
