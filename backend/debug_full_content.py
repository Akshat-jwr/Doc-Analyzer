import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.pdf import PDF
from models.table import Table
from utils.pydantic_objectid import PyObjectId
from db.database import connect_to_mongo
import chromadb
from chromadb.config import Settings

async def debug_full_document_content(document_id: str):
    """Complete debug of document content vs indexed content"""
    
    # Connect to database
    await connect_to_mongo()
    
    print(f"🔍 COMPREHENSIVE DEBUG for Document: {document_id}")
    print("="*80)
    
    # 1. Get document from MongoDB
    document = await PDF.get(PyObjectId(document_id))
    if not document:
        print("❌ Document not found")
        return
    
    print(f"📄 DOCUMENT: {document.filename}")
    print(f"📊 Page count: {document.page_count}")
    print(f"📋 Processing status: {document.processing_status}")
    
    # 2. Check all possible text sources
    print("\n🔍 CHECKING ALL TEXT SOURCES:")
    
    text_sources = {}
    
    # Check common attributes
    text_attrs = ['content', 'text', 'extracted_text', 'full_text', 'raw_text', 'body', 'page_texts']
    
    for attr in text_attrs:
        if hasattr(document, attr):
            value = getattr(document, attr)
            if value:
                text_sources[attr] = value
                print(f"✅ Found {attr}: {type(value)} - Length: {len(str(value))}")
                if isinstance(value, str):
                    print(f"   Preview: {repr(value[:100])}")
                elif isinstance(value, list):
                    print(f"   List length: {len(value)}")
                    if value and isinstance(value[0], dict):
                        for i, item in enumerate(value[:2]):
                            print(f"   Item {i}: {item}")
            else:
                print(f"❌ {attr}: None or empty")
    
    # 3. Get the actual full text that should be indexed
    print(f"\n📝 EXTRACTING COMPLETE TEXT:")
    
    complete_text = ""
    
    # Try to get from page_texts if it exists
    if hasattr(document, 'page_texts') and document.page_texts:
        print("✅ Using page_texts structure")
        for page_data in document.page_texts:
            if isinstance(page_data, dict):
                page_text = page_data.get('text', '')
                page_num = page_data.get('page_number', 1)
            else:
                page_text = getattr(page_data, 'text', '')
                page_num = getattr(page_data, 'page_number', 1)
            
            complete_text += f"\n--- PAGE {page_num} ---\n{page_text}\n"
            print(f"   Page {page_num}: {len(page_text)} characters")
    
    # Fallback to other text sources
    if not complete_text and text_sources:
        key = max(text_sources.keys(), key=lambda k: len(str(text_sources[k])))
        complete_text = str(text_sources[key])
        print(f"✅ Using {key} as text source")
    
    if complete_text:
        print(f"📊 COMPLETE TEXT STATS:")
        print(f"   Total length: {len(complete_text)} characters")
        print(f"   Word count: {len(complete_text.split())} words")
        print(f"   Lines: {len(complete_text.split(chr(10)))}")
        
        # Show full text sections
        print(f"\n📄 FULL TEXT CONTENT:")
        print("-" * 60)
        print(complete_text)
        print("-" * 60)
    else:
        print("❌ No text content found!")
        return
    
    # 4. Simulate proper chunking
    print(f"\n🔪 TESTING CHUNKING:")
    
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=300,
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""]
    )
    
    chunks = splitter.split_text(complete_text)
    
    print(f"📊 CHUNKING RESULTS:")
    print(f"   Number of chunks: {len(chunks)}")
    print(f"   Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} chars")
    
    for i, chunk in enumerate(chunks):
        print(f"\n📝 CHUNK {i+1}:")
        print(f"   Length: {len(chunk)} characters")
        print(f"   Words: {len(chunk.split())} words")
        print(f"   Content: {repr(chunk[:100])}...")
        print(f"   Ends with: {repr(chunk[-50:])}")
    
    # 5. Check what's actually in ChromaDB
    print(f"\n🗄️ CHECKING CHROMADB CONTENT:")
    
    try:
        chroma_client = chromadb.PersistentClient(
            path="./storage/vectors/general",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Try different collection names
        collection_names = ["general_documents", "fixed_documents", "ultimate_documents"]
        
        for collection_name in collection_names:
            try:
                collection = chroma_client.get_collection(collection_name)
                
                results = collection.get(
                    where={"document_id": document_id},
                    include=["documents", "metadatas"]
                )
                
                if results and results.get('ids'):
                    print(f"✅ Found {len(results['ids'])} chunks in '{collection_name}'")
                    
                    text_chunks = 0
                    table_chunks = 0
                    
                    for i, (chunk_id, content, metadata) in enumerate(zip(
                        results['ids'], 
                        results['documents'], 
                        results['metadatas']
                    )):
                        content_type = metadata.get('content_type', 'unknown')
                        
                        if content_type == 'text':
                            text_chunks += 1
                        else:
                            table_chunks += 1
                        
                        print(f"\n   📝 INDEXED CHUNK {i+1}:")
                        print(f"      ID: {chunk_id}")
                        print(f"      Type: {content_type}")
                        print(f"      Page: {metadata.get('page_number', 'unknown')}")
                        print(f"      Length: {len(content)} chars")
                        print(f"      Content: {repr(content[:150])}...")
                    
                    print(f"\n   📊 INDEXED SUMMARY:")
                    print(f"      Text chunks: {text_chunks}")
                    print(f"      Table chunks: {table_chunks}")
                    print(f"      Total indexed: {len(results['ids'])}")
                    
                    # Calculate coverage
                    total_indexed_text = sum(len(doc) for doc, meta in zip(results['documents'], results['metadatas']) if meta.get('content_type') == 'text')
                    coverage_percent = (total_indexed_text / len(complete_text)) * 100 if complete_text else 0
                    
                    print(f"      Coverage: {coverage_percent:.1f}% of original text")
                    
                    break
                
            except Exception as e:
                print(f"❌ Collection '{collection_name}' not found: {e}")
        
    except Exception as e:
        print(f"❌ ChromaDB error: {e}")
    
    # 6. Test semantic search
    print(f"\n🔍 TESTING SEMANTIC SEARCH:")
    
    test_queries = [
        "What projects did Akshat work on?",
        "Tell me about education",
        "Campus Ambassador Portal",
        "Kshitij project"
    ]
    
    try:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        for query in test_queries:
            print(f"\n🔎 Query: '{query}'")
            
            try:
                query_embedding = embedding_model.encode([query]).tolist()
                
                search_results = collection.query(
                    query_embeddings=query_embedding,
                    n_results=3,
                    where={"document_id": document_id}
                )
                
                if search_results and search_results['documents'][0]:
                    print(f"   ✅ Found {len(search_results['documents'][0])} relevant chunks")
                    for i, (doc, meta, dist) in enumerate(zip(
                        search_results['documents'][0],
                        search_results['metadatas'][0],
                        search_results['distances'][0]
                    )):
                        relevance = 1 - dist
                        print(f"      Result {i+1}: {relevance:.3f} relevance - {repr(doc[:100])}...")
                else:
                    print(f"   ❌ No relevant chunks found")
                    
            except Exception as e:
                print(f"   ❌ Search failed: {e}")
        
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")

if __name__ == "__main__":
    document_id = "6843d81f62baed41932b8e65"
    asyncio.run(debug_full_document_content(document_id))
