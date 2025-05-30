import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any

from auth.dependencies import get_current_active_user
from models.user import User
from models.pdf import PDF
from services.pdf_service import process_pdf_async
from services.storage_service import storage_service

router = APIRouter(prefix="/pdf", tags=["PDF Processing"])

class ProcessingResponse(BaseModel):
    success: bool
    message: str
    pdf_id: str = None
    processing_time: float = None
    pages_processed: int = None
    images_extracted: int = None
    tables_extracted: int = None
    cloudinary_url: str = None

class PDFListResponse(BaseModel):
    id: str
    filename: str
    page_count: int
    processing_status: str
    uploaded_at: str
    cloudinary_url: str

@router.post("/upload", response_model=ProcessingResponse)
async def upload_and_process_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and process a PDF document with authentication
    
    Requires:
    - Valid authentication token
    - PDF file (other document types allowed but PDF preferred)
    - File size under 50MB
    """
    
    # Validate file type (done by storage service)
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOC, and DOCX files are supported"
        )
    
    # Create temporary file for processing
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Process the PDF
        result = await process_pdf_async(
            pdf_path=temp_file_path,
            filename=file.filename,
            user_id=str(current_user.id)
        )
        
        if result["success"]:
            return ProcessingResponse(
                success=True,
                message="PDF processed successfully",
                pdf_id=result["pdf_id"],
                processing_time=result["processing_time"],
                pages_processed=result["pages_processed"],
                images_extracted=result["images_extracted"],
                tables_extracted=result["tables_extracted"],
                cloudinary_url=result.get("cloudinary_url")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"PDF processing failed: {result.get('error', 'Unknown error')}"
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

@router.get("/list", response_model=List[PDFListResponse])
async def list_user_pdfs(
    current_user: User = Depends(get_current_active_user)
):
    """Get all PDFs uploaded by the current user"""
    
    user_pdfs = await PDF.find(
        PDF.user_id == current_user.id
    ).sort(-PDF.uploaded_at).to_list()
    
    return [
        PDFListResponse(
            id=str(pdf.id),
            filename=pdf.filename,
            page_count=pdf.page_count,
            processing_status=pdf.processing_status.value,
            uploaded_at=pdf.uploaded_at.isoformat(),
            cloudinary_url=pdf.cloudinary_url
        )
        for pdf in user_pdfs
    ]

@router.get("/{pdf_id}")
async def get_pdf_details(
    pdf_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific PDF"""
    
    try:
        from utils.pydantic_objectid import PyObjectId
        pdf = await PDF.get(PyObjectId(pdf_id))
        
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Check if user owns this PDF
        if pdf.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get related data
        from models.page_text import PageText
        from models.table import Table
        from models.image import Image
        
        page_texts = await PageText.find(PageText.pdf_id == pdf.id).to_list()
        tables = await Table.find(Table.pdf_id == pdf.id).to_list()
        images = await Image.find(Image.pdf_id == pdf.id).to_list()
        
        return {
            "pdf": {
                "id": str(pdf.id),
                "filename": pdf.filename,
                "page_count": pdf.page_count,
                "processing_status": pdf.processing_status.value,
                "uploaded_at": pdf.uploaded_at.isoformat(),
                "cloudinary_url": pdf.cloudinary_url
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
        raise HTTPException(status_code=400, detail="Invalid PDF ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{pdf_id}")
async def delete_pdf(
    pdf_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a PDF and all its associated data"""
    
    try:
        from utils.pydantic_objectid import PyObjectId
        pdf = await PDF.get(PyObjectId(pdf_id))
        
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Check if user owns this PDF
        if pdf.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete from Cloudinary
        public_id = pdf.cloudinary_url.split('/')[-1].split('.')
        storage_service.delete_file(public_id, "raw")
        
        # Delete related data
        from models.page_text import PageText
        from models.table import Table
        from models.image import Image
        
        # Delete page texts
        page_texts = await PageText.find(PageText.pdf_id == pdf.id).to_list()
        for pt in page_texts:
            await pt.delete()
        
        # Delete tables
        tables = await Table.find(Table.pdf_id == pdf.id).to_list()
        for table in tables:
            await table.delete()
        
        # Delete images (and their Cloudinary files)
        images = await Image.find(Image.pdf_id == pdf.id).to_list()
        for img in images:
            img_public_id = img.cloudinary_url.split('/')[-1].split('.')
            storage_service.delete_file(img_public_id, "image")
            await img.delete()
        
        # Delete PDF record
        await pdf.delete()
        
        return {"message": "PDF and all associated data deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid PDF ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
