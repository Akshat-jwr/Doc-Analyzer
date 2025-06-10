import os
import tempfile
import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, WebSocket
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json

from auth.dependencies import get_current_active_user
from models.user import User
from models.pdf import PDF, ProcessingStatus
from services.pdf_service import process_pdf_phase_1_async
from services import extract_tables_background
from services.storage_service import storage_service
from services.chatbot_handler import ChatbotModeHandler

router = APIRouter(prefix="/documents", tags=["Document Processing"])  # 🔥 UPDATED: Changed from /pdf to /documents

class ProcessingResponse(BaseModel):
    success: bool
    message: str
    phase: str
    document_id: str = None  # 🔥 UPDATED: Changed from pdf_id to document_id
    processing_time: float = None
    pages_processed: int = None
    images_extracted: int = None
    general_queries_ready: bool = False
    analytical_queries_ready: bool = False
    cloudinary_url: str = None
    status: str = None

class DocumentListResponse(BaseModel):  # 🔥 UPDATED: Changed from PDFListResponse
    id: str
    filename: str
    page_count: int
    processing_status: str
    uploaded_at: str
    cloudinary_url: str
    tables_processed: int = 0
    total_tables_found: int = 0

class DocumentStatusResponse(BaseModel):  # 🔥 UPDATED: Changed from PDFStatusResponse
    document_id: str  # 🔥 UPDATED: Changed from pdf_id
    filename: str
    processing_status: str
    pages: int
    tables_processed: int
    total_tables: int
    general_queries_ready: bool
    analytical_queries_ready: bool
    message: str
    progress_percentage: float = 0.0

class ChatQueryRequest(BaseModel):
    query: str
    mode: str  # "general", "analytical", "visualization"
    page_context: Optional[int] = None

class ChatQueryResponse(BaseModel):
    mode: str
    response: str
    ready: bool
    error: Optional[str] = None
    tables: Optional[List[Dict]] = None
    source_pages: Optional[List[int]] = None
    chart_data: Optional[Dict] = None

# Initialize chatbot handler
chatbot_handler = ChatbotModeHandler()

@router.post("/upload", response_model=ProcessingResponse)
async def upload_and_process_document(  # 🔥 UPDATED: Changed function name
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    🔥 UPDATED: Upload and process Documents - Phase 1 (Fast: Text + Images only)
    Background table extraction starts automatically
    
    Supports: PDF, Word (DOC/DOCX), Spreadsheets (CSV/XLSX/XLS), Images (PNG/JPG/JPEG)
    
    Requires:
    - Valid authentication token
    - Supported document file
    - File size under 50MB
    """
    
    # 🔥 UPDATED: Enhanced file type validation with images
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx', '.csv', '.xlsx', '.xls', '.png', '.jpg', '.jpeg')):
        raise HTTPException(
            status_code=400,
            detail="Supported file types: PDF, Word documents (DOC/DOCX), Spreadsheets (CSV/XLSX/XLS), Images (PNG/JPG/JPEG)"
        )
    
    # Create temporary file for processing
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Phase 1: Fast processing (text + images only)
        result = await process_pdf_phase_1_async(  # Note: Keep function name for now to avoid breaking changes
            pdf_path=temp_file_path,
            filename=file.filename,
            user_id=str(current_user.id)
        )
        
        if result["success"]:
            # Start background table extraction for supported file types (don't await - let it run in background)
            if result.get("background_processing", False):
                asyncio.create_task(extract_tables_background(result["pdf_id"]))  # Keep pdf_id for compatibility
            
            return ProcessingResponse(
                success=True,
                message="Phase 1 complete! General queries ready. Analytics loading in background..." if result.get("background_processing") else "Document processing complete! All features ready.",
                phase=result["phase"],
                document_id=result["pdf_id"],  # Map pdf_id to document_id
                processing_time=result["processing_time"],
                pages_processed=result["pages_processed"],
                images_extracted=result["images_extracted"],
                general_queries_ready=result["general_queries_ready"],
                analytical_queries_ready=result["analytical_queries_ready"],
                cloudinary_url=result.get("cloudinary_url"),
                status=result.get("status")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {result.get('error', 'Unknown error')}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during processing: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not cleanup temp directory: {e}")

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)  # 🔥 UPDATED: Changed parameter name
async def get_document_status(  # 🔥 UPDATED: Changed function name
    document_id: str,  # 🔥 UPDATED: Changed parameter name
    current_user: User = Depends(get_current_active_user)
):
    """Check document processing status for real-time updates"""  # 🔥 UPDATED: Updated docstring
    try:
        from utils.pydantic_objectid import PyObjectId
        document = await PDF.get(PyObjectId(document_id))  # Keep PDF model for now
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")  # 🔥 UPDATED: Error message
        
        # Check if user owns this document
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Status mapping
        status_mapping = {
            ProcessingStatus.UPLOADED: {
                "general_queries_ready": False,
                "analytical_queries_ready": False,
                "message": "Processing started..."
            },
            ProcessingStatus.PROCESSING: {
                "general_queries_ready": False,
                "analytical_queries_ready": False,
                "message": "Processing text and images..."
            },
            ProcessingStatus.TEXT_IMAGES_COMPLETE: {
                "general_queries_ready": True,
                "analytical_queries_ready": False,
                "message": "✅ General queries ready! Analytics loading in background..."
            },
            ProcessingStatus.BACKGROUND_PROCESSING: {
                "general_queries_ready": True,
                "analytical_queries_ready": False,
                "message": f"🔄 Analyzing tables... ({document.tables_processed}/{document.total_tables_found} processed)"
            },
            ProcessingStatus.COMPLETED: {
                "general_queries_ready": True,
                "analytical_queries_ready": True,
                "message": "🎉 All features ready! Analytics and visualizations available."
            },
            ProcessingStatus.FAILED: {
                "general_queries_ready": False,
                "analytical_queries_ready": False,
                "message": f"❌ Processing failed: {document.background_error or 'Unknown error'}"
            }
        }
        
        status_info = status_mapping.get(document.processing_status, {
            "general_queries_ready": False,
            "analytical_queries_ready": False,
            "message": "Unknown status"
        })
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if document.processing_status == ProcessingStatus.TEXT_IMAGES_COMPLETE:
            progress_percentage = 50.0  # Phase 1 complete
        elif document.processing_status == ProcessingStatus.BACKGROUND_PROCESSING:
            if document.total_tables_found > 0:
                progress_percentage = 50.0 + (document.tables_processed / document.total_tables_found) * 50.0
            else:
                progress_percentage = 75.0  # Assume halfway through background processing
        elif document.processing_status == ProcessingStatus.COMPLETED:
            progress_percentage = 100.0
        
        return DocumentStatusResponse(
            document_id=str(document.id),  # 🔥 UPDATED: Changed field name
            filename=document.filename,
            processing_status=document.processing_status.value,
            pages=document.page_count,
            tables_processed=document.tables_processed,
            total_tables=document.total_tables_found,
            progress_percentage=progress_percentage,
            **status_info
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")  # 🔥 UPDATED: Error message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/{document_id}/progress")  # 🔥 UPDATED: Changed parameter name
async def websocket_document_progress(websocket: WebSocket, document_id: str):  # 🔥 UPDATED: Changed function and parameter names
    """WebSocket endpoint for real-time document processing updates"""  # 🔥 UPDATED: Updated docstring
    await websocket.accept()
    
    try:
        from utils.pydantic_objectid import PyObjectId
        
        while True:
            # Get current status
            document = await PDF.get(PyObjectId(document_id))  # Keep PDF model for now
            if not document:
                await websocket.send_text(json.dumps({"error": "Document not found"}))  # 🔥 UPDATED: Error message
                break
            
            # Calculate progress
            progress_percentage = 0.0
            if document.processing_status == ProcessingStatus.TEXT_IMAGES_COMPLETE:
                progress_percentage = 50.0
            elif document.processing_status == ProcessingStatus.BACKGROUND_PROCESSING:
                if document.total_tables_found > 0:
                    progress_percentage = 50.0 + (document.tables_processed / document.total_tables_found) * 50.0
                else:
                    progress_percentage = 75.0
            elif document.processing_status == ProcessingStatus.COMPLETED:
                progress_percentage = 100.0
            
            # Send status update
            status_update = {
                "processing_status": document.processing_status.value,
                "tables_processed": document.tables_processed,
                "total_tables": document.total_tables_found,
                "progress_percentage": progress_percentage,
                "general_queries_ready": document.processing_status in [
                    ProcessingStatus.TEXT_IMAGES_COMPLETE,
                    ProcessingStatus.BACKGROUND_PROCESSING,
                    ProcessingStatus.COMPLETED
                ],
                "analytical_queries_ready": document.processing_status == ProcessingStatus.COMPLETED
            }
            
            await websocket.send_text(json.dumps(status_update))
            
            # Break if processing is complete or failed
            if document.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                break
            
            # Wait before next update
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
    finally:
        await websocket.close()

@router.post("/{document_id}/chat", response_model=ChatQueryResponse)  # 🔥 UPDATED: Changed parameter name
async def chat_with_document(  # 🔥 UPDATED: Changed function name
    document_id: str,  # 🔥 UPDATED: Changed parameter name
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Chat with document using different modes"""  # 🔥 UPDATED: Updated docstring
    try:
        from utils.pydantic_objectid import PyObjectId
        document = await PDF.get(PyObjectId(document_id))  # Keep PDF model for now
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")  # 🔥 UPDATED: Error message
        
        # Check if user owns this document
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Handle query using chatbot handler (keep pdf_id for internal compatibility)
        result = await chatbot_handler.handle_query(
            pdf_id=document_id,  # Internal systems still use pdf_id
            query=request.query,
            mode=request.mode,
            page_context=request.page_context
        )
        
        if "error" in result:
            return ChatQueryResponse(
                mode=request.mode,
                response="",
                ready=False,
                error=result["error"]
            )
        
        return ChatQueryResponse(
            mode=result["mode"],
            response=result["response"],
            ready=result["ready"],
            tables=result.get("tables"),
            source_pages=result.get("source_pages"),
            chart_data=result.get("data")
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")  # 🔥 UPDATED: Error message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[DocumentListResponse])  # 🔥 UPDATED: Changed response model
async def list_user_documents(  # 🔥 UPDATED: Changed function name
    current_user: User = Depends(get_current_active_user)
):
    """Get all documents uploaded by the current user with processing status"""  # 🔥 UPDATED: Updated docstring
    
    user_documents = await PDF.find(  # Keep PDF model for now
        PDF.user_id == current_user.id
    ).sort(-PDF.uploaded_at).to_list()
    
    return [
        DocumentListResponse(  # 🔥 UPDATED: Changed response class
            id=str(doc.id),
            filename=doc.filename,
            page_count=doc.page_count,
            processing_status=doc.processing_status.value,
            uploaded_at=doc.uploaded_at.isoformat(),
            cloudinary_url=doc.cloudinary_url,
            tables_processed=doc.tables_processed,
            total_tables_found=doc.total_tables_found
        )
        for doc in user_documents  # 🔥 UPDATED: Changed variable name
    ]

@router.get("/{document_id}")  # 🔥 UPDATED: Changed parameter name
async def get_document_details(  # 🔥 UPDATED: Changed function name
    document_id: str,  # 🔥 UPDATED: Changed parameter name
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific document"""  # 🔥 UPDATED: Updated docstring
    
    try:
        from utils.pydantic_objectid import PyObjectId
        document = await PDF.get(PyObjectId(document_id))  # Keep PDF model for now
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")  # 🔥 UPDATED: Error message
        
        # Check if user owns this document
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get related data
        from models.page_text import PageText
        from models.table import Table
        from models.image import Image
        
        page_texts = await PageText.find(PageText.pdf_id == document.id).to_list()
        tables = await Table.find(Table.pdf_id == document.id).to_list()
        images = await Image.find(Image.pdf_id == document.id).to_list()
        
        return {
            "document": {  # 🔥 UPDATED: Changed from "pdf" to "document"
                "id": str(document.id),
                "filename": document.filename,
                "page_count": document.page_count,
                "processing_status": document.processing_status.value,
                "uploaded_at": document.uploaded_at.isoformat(),
                "cloudinary_url": document.cloudinary_url,
                "tables_processed": document.tables_processed,
                "total_tables_found": document.total_tables_found,
                "text_images_completed_at": document.text_images_completed_at.isoformat() if document.text_images_completed_at else None,
                "fully_completed_at": document.fully_completed_at.isoformat() if document.fully_completed_at else None
            },
            "processing_info": {
                "general_queries_ready": document.processing_status in [
                    ProcessingStatus.TEXT_IMAGES_COMPLETE,
                    ProcessingStatus.BACKGROUND_PROCESSING,
                    ProcessingStatus.COMPLETED
                ],
                "analytical_queries_ready": document.processing_status == ProcessingStatus.COMPLETED,
                "background_error": document.background_error
            },
            "page_texts": [
                {
                    "page_number": pt.page_number,
                    "text": pt.extracted_text[:500] + "..." if len(pt.extracted_text) > 500 else pt.extracted_text
                }
                for pt in sorted(page_texts, key=lambda x: x.page_number)
            ],
            "tables": [
                {
                    "id": str(table.id),
                    "title": table.table_title,
                    "start_page": table.start_page,
                    "end_page": table.end_page,
                    "column_count": table.column_count,
                    "row_count": table.row_count,
                    "markdown_preview": table.markdown_content[:200] + "..." if len(table.markdown_content) > 200 else table.markdown_content
                }
                for table in tables
            ],
            "images": [
                {
                    "page_number": img.page_number,
                    "cloudinary_url": img.cloudinary_url
                }
                for img in sorted(images, key=lambda x: x.page_number)
            ]
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")  # 🔥 UPDATED: Error message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")  # 🔥 UPDATED: Changed parameter name
async def delete_document(  # 🔥 UPDATED: Changed function name
    document_id: str,  # 🔥 UPDATED: Changed parameter name
    current_user: User = Depends(get_current_active_user)
):
    """Delete a document and all its associated data"""  # 🔥 UPDATED: Updated docstring
    
    try:
        from utils.pydantic_objectid import PyObjectId
        document = await PDF.get(PyObjectId(document_id))  # Keep PDF model for now
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")  # 🔥 UPDATED: Error message
        
        # Check if user owns this document
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        from services.multi_chat_service import multi_chat_service
        chunk_deletion_result = await multi_chat_service.delete_document_chunks(document_id)
        
        
        # Delete from Cloudinary
        try:
            public_id = document.cloudinary_url.split('/')[-1].split('.')[0]
            storage_service.delete_file(public_id, "raw")
        except Exception as e:
            print(f"Warning: Could not delete document from Cloudinary: {e}")  # 🔥 UPDATED: Log message
        
        # Delete related data
        from models.page_text import PageText
        from models.table import Table
        from models.image import Image
        
        # Delete page texts
        page_texts = await PageText.find(PageText.pdf_id == document.id).to_list()
        for pt in page_texts:
            await pt.delete()
        
        # Delete tables
        tables = await Table.find(Table.pdf_id == document.id).to_list()
        for table in tables:
            await table.delete()
        
        # Delete images (and their Cloudinary files)
        images = await Image.find(Image.pdf_id == document.id).to_list()
        for img in images:
            try:
                img_public_id = img.cloudinary_url.split('/')[-1].split('.')[0]
                storage_service.delete_file(img_public_id, "image")
            except Exception as e:
                print(f"Warning: Could not delete image from Cloudinary: {e}")
            await img.delete()
        
        # Delete document record
        await document.delete()
        
        return {"message": "Document and all associated data deleted successfully"}  # 🔥 UPDATED: Success message
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")  # 🔥 UPDATED: Error message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/force-table-extraction")  # 🔥 UPDATED: Changed parameter name
async def force_table_extraction(
    document_id: str,  # 🔥 UPDATED: Changed parameter name
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger table extraction if it failed or was skipped"""
    try:
        from utils.pydantic_objectid import PyObjectId
        document = await PDF.get(PyObjectId(document_id))  # Keep PDF model for now
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")  # 🔥 UPDATED: Error message
        
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if document.processing_status == ProcessingStatus.COMPLETED:
            return {"message": "Table extraction already completed"}
        
        if document.processing_status == ProcessingStatus.BACKGROUND_PROCESSING:
            return {"message": "Table extraction already in progress"}
        
        # Start table extraction (keep pdf_id for internal compatibility)
        asyncio.create_task(extract_tables_background(document_id))
        
        return {"message": "Table extraction started manually"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")  # 🔥 UPDATED: Error message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
