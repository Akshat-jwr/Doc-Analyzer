import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.pdf import PDF
from models.table import Table
from utils.pydantic_objectid import PyObjectId
from db.database import connect_to_mongo  # ✅ Initialize database first

async def debug_document_structure(document_id: str):
    """Debug document structure to understand the data format"""
    
    print(f"🔍 Debugging document {document_id}")
    
    # ✅ CRITICAL: Initialize database connection first
    try:
        await connect_to_mongo()
        print("✅ Database connected successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Get document
    try:
        document = await PDF.get(PyObjectId(document_id))
        if not document:
            print("❌ Document not found")
            return
    except Exception as e:
        print(f"❌ Error getting document: {e}")
        return
    
    print("📄 DOCUMENT INFO:")
    print(f"  - ID: {document.id}")
    print(f"  - Filename: {document.filename}")
    
    # ✅ Check all possible content attributes
    content_attrs = ['content', 'text', 'extracted_text', 'full_text', 'raw_text', 'body']
    content_found = False
    
    for attr in content_attrs:
        if hasattr(document, attr):
            content = getattr(document, attr)
            print(f"  - Has {attr}: {content is not None}")
            
            if content and isinstance(content, str):
                content_found = True
                print(f"  - {attr} type: {type(content)}")
                print(f"  - {attr} length: {len(content)}")
                print(f"  - Contains PAGE markers: {'--- PAGE' in content}")
                print(f"  - {attr} preview (first 300 chars):")
                print(f"    {repr(content[:300])}")
                
                if '\n--- PAGE' in content:
                    pages = content.split('\n--- PAGE')
                    print(f"  - Number of page sections: {len(pages)}")
                    for i, page in enumerate(pages[:3]):
                        print(f"    Page section {i}: {len(page)} chars")
                        if page.strip():
                            print(f"      Preview: {repr(page[:100])}")
                break
    
    if not content_found:
        print("❌ No text content found in any expected attributes")
        
        # Check document dictionary representation
        print("📋 Document fields available:")
        if hasattr(document, '__dict__'):
            for key, value in document.__dict__.items():
                if isinstance(value, str) and len(value) > 10:
                    print(f"  - {key}: {type(value)} (length: {len(value)})")
                else:
                    print(f"  - {key}: {type(value)} = {value}")
    
    # Get tables
    try:
        tables = await Table.find(Table.pdf_id == PyObjectId(document_id)).to_list()
        print(f"\n📊 TABLES INFO:")
        print(f"  - Number of tables: {len(tables)}")
        
        for i, table in enumerate(tables[:3]):
            print(f"  Table {i+1}:")
            print(f"    - ID: {table.id}")
            print(f"    - Title: {table.table_title}")
            print(f"    - Page: {table.start_page}")
            print(f"    - Dimensions: {table.row_count}x{table.column_count}")
            print(f"    - Has markdown: {bool(table.markdown_content)}")
            if table.markdown_content:
                print(f"    - Markdown length: {len(table.markdown_content)}")
                print(f"    - Markdown preview: {repr(table.markdown_content[:150])}")
    except Exception as e:
        print(f"❌ Error getting tables: {e}")

# Run this with your document ID
if __name__ == "__main__":
    # ✅ Use the actual document ID from your API
    document_id = "6842c94f991a8bf1f1b6efac"  # Your resume document
    asyncio.run(debug_document_structure(document_id))
