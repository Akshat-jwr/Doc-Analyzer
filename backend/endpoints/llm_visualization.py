# endpoints/llm_visualization.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field
from services.llm_visualization_service import LLMVisualizationService, LLMVisualizationRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm-visualization", tags=["llm-visualization"])
service = LLMVisualizationService()

class LLMCreateRequest(BaseModel):
    document_id: str = Field(..., description="Document ID")
    query: str = Field(..., description="Visualization request (e.g., 'create a pie chart of table 29')")
    page_number: Optional[int] = Field(None, description="Specific page (None for smart search)")
    user_id: str = Field(..., description="User ID")

@router.post("/create")
async def create_llm_visualization(request: LLMCreateRequest):
    """Create LLM-generated visualization"""
    try:
        logger.info(f"🎨 Creating LLM visualization: {request.query}")
        
        viz_request = LLMVisualizationRequest(
            document_id=request.document_id,
            query=request.query,
            page_number=request.page_number,
            user_id=request.user_id
        )
        
        result = await service.create_visualization(viz_request)
        return result
        
    except Exception as e:
        logger.error(f"LLM visualization endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_llm_history(
    user_id: str = Query(..., description="User ID"),
    document_id: Optional[str] = Query(None, description="Filter by document"),
    limit: int = Query(50, ge=1, le=100)
):
    """Get LLM visualization history"""
    try:
        history = await service.get_history(user_id, document_id, limit)
        return {
            "success": True,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"LLM history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/details/{viz_id}")
async def get_llm_details(
    viz_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Get LLM visualization details with image"""
    try:
        result = await service.get_details(viz_id, user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{viz_id}")
async def delete_llm_visualization(
    viz_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Delete LLM visualization"""
    try:
        result = await service.delete_viz(viz_id, user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def llm_health_check():
    """Health check for LLM visualization service"""
    return {"status": "healthy", "service": "llm-visualization"}
