from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from models.user import User
from models.table import Table
from models.pdf import PDF
from auth.dependencies import get_current_active_user
from utils.pydantic_objectid import PyObjectId

router = APIRouter(prefix="/tables", tags=["Tables"])

@router.get("/document/{document_id}")
async def get_document_tables(
    document_id: str,
    page: Optional[int] = Query(1, ge=1),
    limit: Optional[int] = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tables from a specific document with pagination and search"""
    try:
        # Verify document exists and user has access
        document = await PDF.get(PyObjectId(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build base query for document tables
        base_query = Table.find(Table.pdf_id == PyObjectId(document_id))
        
        # Add search filter if provided
        if search:
            # Create search query with regex for title and content
            search_query = base_query.find({
                "$or": [
                    {"table_title": {"$regex": search, "$options": "i"}},
                    {"markdown_content": {"$regex": search, "$options": "i"}}
                ]
            })
        else:
            search_query = base_query
        
        # ✅ FIX: Get total count using the correct method
        total_tables = await search_query.count()
        
        # Get paginated tables
        skip = (page - 1) * limit
        tables = await search_query.sort(Table.table_number).skip(skip).limit(limit).to_list()
        
        # Format response
        table_list = []
        for table in tables:
            table_data = {
                "id": str(table.id),
                "title": table.table_title,
                "table_number": table.table_number,
                "start_page": table.start_page,
                "end_page": table.end_page,
                "column_count": table.column_count,
                "row_count": table.row_count,
                "markdown_content": table.markdown_content,
                "created_at": table.created_at.isoformat() if hasattr(table, 'created_at') and table.created_at else None
            }
            table_list.append(table_data)
        
        return {
            "success": True,
            "tables": table_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_tables,
                "pages": (total_tables + limit - 1) // limit
            },
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "total_tables": total_tables
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        print(f"Error in get_document_tables: {e}")  # Debug logging
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}/summary")
async def get_document_tables_summary(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get summary of tables in a document"""
    try:
        # Verify document exists and user has access
        document = await PDF.get(PyObjectId(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # ✅ FIX: Get all tables using proper query method
        tables = await Table.find(Table.pdf_id == PyObjectId(document_id)).to_list()
        
        # Calculate summary stats
        total_tables = len(tables)
        total_rows = sum(table.row_count for table in tables if table.row_count)
        total_columns = sum(table.column_count for table in tables if table.column_count)
        avg_columns = total_columns / total_tables if total_tables > 0 else 0
        
        # Get pages that contain tables
        pages_with_tables = list(set(table.start_page for table in tables if table.start_page))
        pages_with_tables.sort()
        
        return {
            "success": True,
            "summary": {
                "total_tables": total_tables,
                "total_rows": total_rows,
                "total_columns": total_columns,
                "average_columns": round(avg_columns, 1),
                "pages_with_tables": pages_with_tables,
                "page_count": len(pages_with_tables)
            },
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "page_count": document.page_count
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        print(f"Error in get_document_tables_summary: {e}")  # Debug logging
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{table_id}")
async def get_single_table(
    table_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a single table by ID"""
    try:
        table = await Table.get(PyObjectId(table_id))
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Check if user owns the document containing this table
        document = await PDF.get(table.pdf_id)
        if not document or document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "table": {
                "id": str(table.id),
                "title": table.table_title,
                "table_number": table.table_number,
                "start_page": table.start_page,
                "end_page": table.end_page,
                "column_count": table.column_count,
                "row_count": table.row_count,
                "markdown_content": table.markdown_content,
                "created_at": table.created_at.isoformat() if hasattr(table, 'created_at') and table.created_at else None
            },
            "document": {
                "id": str(document.id),
                "filename": document.filename
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid table ID")
    except Exception as e:
        print(f"Error in get_single_table: {e}")  # Debug logging
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document/{document_id}/export")
async def export_document_tables(
    document_id: str,
    format: str = Query("markdown", regex="^(markdown|csv|json)$"),
    current_user: User = Depends(get_current_active_user)
):
    """Export all tables from a document in specified format"""
    try:
        # Verify document exists and user has access
        document = await PDF.get(PyObjectId(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # ✅ FIX: Get all tables using proper query method
        tables = await Table.find(Table.pdf_id == PyObjectId(document_id)).sort(Table.table_number).to_list()
        
        if not tables:
            raise HTTPException(status_code=404, detail="No tables found in this document")
        
        if format == "markdown":
            content = f"# Tables from {document.filename}\n\n"
            for table in tables:
                content += f"## {table.table_title}\n\n"
                content += f"**Page:** {table.start_page}"
                if table.start_page != table.end_page:
                    content += f"-{table.end_page}"
                content += f" | **Rows:** {table.row_count} | **Columns:** {table.column_count}\n\n"
                content += f"{table.markdown_content}\n\n---\n\n"
            
            return {
                "success": True,
                "format": "markdown",
                "content": content,
                "filename": f"{document.filename.replace('.', '_')}_tables.md"
            }
        
        elif format == "json":
            tables_data = []
            for table in tables:
                tables_data.append({
                    "id": str(table.id),
                    "title": table.table_title,
                    "table_number": table.table_number,
                    "start_page": table.start_page,
                    "end_page": table.end_page,
                    "column_count": table.column_count,
                    "row_count": table.row_count,
                    "markdown_content": table.markdown_content
                })
            
            return {
                "success": True,
                "format": "json",
                "content": tables_data,
                "filename": f"{document.filename.replace('.', '_')}_tables.json"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        print(f"Error in export_document_tables: {e}")  # Debug logging
        raise HTTPException(status_code=500, detail=str(e))
