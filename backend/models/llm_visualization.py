# models/llm_visualization.py - FIXED page_number validation
from beanie import Document
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.pydantic_objectid import PyObjectId

class LLMVisualization(Document):
    """Fixed LLM visualization - allows page_number=0 for intelligent search"""
    
    # ✅ FIX: Allow page_number=0 for intelligent search
    user_id: PyObjectId = Field(..., index=True)
    document_id: PyObjectId = Field(..., index=True)
    query: str = Field(..., min_length=1, max_length=1000)
    page_number: Optional[int] = Field(None, ge=0)  # ✅ CHANGED: ge=0 instead of ge=1
    
    # Discovery results
    matching_chunks: List[Dict] = Field(default_factory=list)
    matching_pages: List[int] = Field(default_factory=list)
    selected_tables: List[Dict] = Field(default_factory=list)
    
    # LLM results
    chart_type: str = Field(default="unknown")
    success: bool = Field(default=False, index=True)
    image_base64: Optional[str] = Field(None)
    llm_description: Optional[str] = Field(None)
    error_message: Optional[str] = Field(None)
    
    # Metadata
    processing_time_ms: int = Field(default=0, ge=0)
    llm_model_used: str = Field(default="gemini-1.5-pro")
    total_chunks_searched: int = Field(default=0, ge=0)
    total_tables_found: int = Field(default=0, ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, index=True)

    class Settings:
        name = "llm_visualizations"

    @validator('user_id', 'document_id', pre=True)
    def validate_object_ids(cls, v):
        """Ensure ObjectIds are properly converted"""
        if isinstance(v, str):
            try:
                return PyObjectId(v)
            except Exception:
                raise ValueError(f"Invalid ObjectId: {v}")
        return v
    
    # ✅ NEW: Custom validator for page_number logic
    @validator('page_number')
    def validate_page_number(cls, v):
        """Allow 0 for intelligent search, or positive integers for specific pages"""
        if v is not None and v < 0:
            raise ValueError("Page number must be 0 (for intelligent search) or positive integer")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "document_id": str(self.document_id),
            "query": self.query,
            "page_number": self.page_number,
            "search_method": "intelligent" if self.page_number == 0 else "specific_page",
            "chart_type": self.chart_type,
            "success": self.success,
            "has_image": bool(self.image_base64),
            "llm_description": self.llm_description,
            "error_message": self.error_message,
            "matching_pages": self.matching_pages,
            "tables_count": len(self.selected_tables),
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat()
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Full dict including image"""
        data = self.to_dict()
        data["image_base64"] = self.image_base64
        return data
