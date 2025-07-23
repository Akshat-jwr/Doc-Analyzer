import os
import logging
import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from models.pdf import PDF
from models.table import Table
from models.image import Image
from models.document_chunk import DocumentChunk
from models.chat_session import ChatMessage, ChatSession, ChatType
from utils.pydantic_objectid import PyObjectId
from datetime import datetime
from scipy.spatial.distance import cosine
import traceback
import uuid
import requests
from PIL import Image as PILImage
import io
import asyncio
import concurrent.futures
import threading
from functools import partial
import matplotlib
import matplotlib.pyplot as plt
import base64
import numpy as np
from io import StringIO
import pandas as pd


# Disable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "false"

logger = logging.getLogger(__name__)

class MultiChatService:
    """
    🚀 COMPLETE: Multi-Chat Service with ENHANCED ANALYTICAL CHAT
    """
    
    def __init__(self):
        # Initialize sentence transformers
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Google Gemini Pro (handles both text and images)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        self.llm_text = genai.GenerativeModel('gemini-2.5-flash')
        # ✅ FASTEST: Use Flash for image analysis (5x faster than Pro)
        self.llm_vision = genai.GenerativeModel('gemini-1.5-pro')
        
        # ✅ THREAD POOL: For parallel image processing
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
        logger.info("✅ COMPLETE Multi-Chat Service with ENHANCED ANALYTICAL CHAT initialized")
    
    # 🚀 ULTRA-FAST PARALLEL IMAGE ANALYSIS
    def _analyze_image_sync(self, image_url: str) -> str:
        """🚀 SYNC: Single image analysis for thread pool"""
        try:
            # Download with aggressive timeout
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image = PILImage.open(io.BytesIO(response.content))
            
            # ✅ AGGRESSIVE OPTIMIZATION: Resize to max 800x800 for speed
            if image.size[0] > 800 or image.size[1] > 800:
                image.thumbnail((800, 800), PILImage.Resampling.LANCZOS)
            
            # ✅ ULTRA-SHORT PROMPT for maximum speed
            prompt = """Analyze this document image quickly:
- Document type
- Key text/data visible
- Charts/tables present
- Main visual elements
Be concise but comprehensive."""
            
            vision_response = self.llm_vision.generate_content([prompt, image])
            return vision_response.text
            
        except Exception as e:
            logger.error(f"❌ Sync image analysis error {image_url}: {e}")
            return f"Image analysis failed: {str(e)}"
    
    async def _analyze_cloudinary_image_ultra_fast(self, image_url: str) -> str:
        """🚀 ULTRA-FAST: Async wrapper for parallel image analysis"""
        try:
            logger.info(f"🖼️ ULTRA-FAST analyzing: {image_url}")
            
            # ✅ THREAD POOL: Run in separate thread for true parallelism
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(
                self.thread_pool, 
                self._analyze_image_sync, 
                image_url
            )
            
            logger.info(f"⚡ ULTRA-FAST analysis complete: {len(analysis)} chars")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ultra-fast analysis error {image_url}: {e}")
            return f"Ultra-fast analysis failed: {str(e)}"
    
    # 🎯 ENHANCED ANALYTICAL FEATURES
    def _extract_page_number_from_query(self, query: str) -> Tuple[Optional[int], str]:
        """🎯 SMART: Extract page number from user query"""
        try:
            # Clean query for analysis
            cleaned_query = query.lower().strip()
            
            # Patterns to detect page references
            page_patterns = [
                r"page\s+(\d+)",
                r"on\s+page\s+(\d+)",
                r"from\s+page\s+(\d+)",
                r"in\s+page\s+(\d+)",
                r"p\.?\s*(\d+)",
                r"pg\s*\.?\s*(\d+)"
            ]
            
            for pattern in page_patterns:
                match = re.search(pattern, cleaned_query)
                if match:
                    page_num = int(match.group(1))
                    
                    # Remove page reference from query for clean analysis
                    clean_query = re.sub(pattern, "", cleaned_query).strip()
                    clean_query = re.sub(r'\s+', ' ', clean_query)  # Remove extra spaces
                    
                    logger.info(f"🎯 Extracted page number: {page_num}")
                    return page_num, clean_query if clean_query else query
            
            # No page number found
            logger.info("🎯 No page number specified - will analyze all tables")
            return None, query
            
        except Exception as e:
            logger.error(f"Error extracting page number: {e}")
            return None, query
    
    async def _get_page_tables(self, document_id: str, page_number: int) -> List[Dict[str, Any]]:
        """📊 Get tables for specific page"""
        try:
            tables = await Table.find(
                Table.pdf_id == PyObjectId(document_id),
                Table.start_page <= page_number,
                Table.end_page >= page_number
            ).to_list()
            
            page_tables = []
            for table in tables:
                page_tables.append({
                    'id': str(table.id),
                    'title': table.table_title or f'Table_{table.table_number}',
                    'markdown_content': table.markdown_content,
                    'row_count': table.row_count,
                    'column_count': table.column_count,
                    'start_page': table.start_page,
                    'end_page': table.end_page
                })
            
            logger.info(f"📊 Found {len(page_tables)} tables for page {page_number}")
            return page_tables
            
        except Exception as e:
            logger.error(f"Error getting page tables: {e}")
            return []
    
    async def _analyze_page_image_for_tables(self, document_id: str, page_number: int, query: str) -> str:
        """🖼️ FALLBACK: Analyze page image when no tables found in DB"""
        try:
            logger.info(f"🖼️ FALLBACK: Analyzing page {page_number} image for tables")
            
            # Get page image
            images = await Image.find(
                Image.pdf_id == PyObjectId(document_id),
                Image.page_number == page_number
            ).to_list()
            
            if not images:
                return f"No image found for page {page_number}. The page may not exist or may not have been processed yet."
            
            image_url = images[0].cloudinary_url
            
            # Download and process image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            image = PILImage.open(io.BytesIO(response.content))
            if image.size[0] > 1024 or image.size[1] > 1024:
                image.thumbnail((1024, 1024), PILImage.Resampling.LANCZOS)
            
            # 🎯 SPECIALIZED TABLE ANALYSIS PROMPT
            table_analysis_prompt = f"""🎯 SPECIALIZED TABLE ANALYSIS for PAGE {page_number}

USER QUERY: "{query}"

MISSION: Analyze this page image specifically for TABLE CONTENT and answer the user's analytical question.

FOCUS AREAS:
1. 📊 IDENTIFY ALL TABLES: Look for any tabular data, structured information, charts with data
2. 📈 EXTRACT TABLE DATA: Convert visual table content to text format
3. 🔍 ANALYZE DATA: Focus on numerical patterns, trends, comparisons
4. 💡 ANSWER QUERY: Provide specific analytical insights related to the user's question

RESPONSE FORMAT:
If tables found:
📊 TABLE ANALYSIS FOR PAGE {page_number}:

**Tables Identified:**
- Table 1: [Title/Description]
- Table 2: [Title/Description] (if any)

**Data Extracted:**
[Convert table data to text format - be precise]

**Analytical Insights:**
[Answer the user's query with specific data points, trends, calculations]

**Key Findings:**
- [Bullet point findings]
- [Numerical insights]
- [Comparative analysis]

If no tables found:
❌ NO TABLES DETECTED on page {page_number}

[Explain what content is visible but note the absence of tabular data]

EXECUTE TABLE ANALYSIS NOW:"""
            
            # Analyze image
            vision_response = self.llm_vision.generate_content([table_analysis_prompt, image])
            analysis = vision_response.text
            
            logger.info(f"✅ Image table analysis complete: {len(analysis)} chars")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in image table analysis: {e}")
            return f"Failed to analyze page {page_number} image: {str(e)}"
    
    async def _handle_table_modification(self, tables: List[Dict], query: str, page_number: Optional[int] = None) -> Dict[str, Any]:
        """🔄 HANDLE TABLE MODIFICATIONS based on user query"""
        try:
            logger.info(f"🔄 Processing table modification request")
            
            # Detect if user wants to modify tables
            modification_keywords = [
                'change', 'modify', 'update', 'edit', 'alter', 'adjust',
                'add', 'remove', 'delete', 'insert', 'replace',
                'create new', 'make new', 'generate new', 'build new'
            ]
            
            query_lower = query.lower()
            is_modification = any(keyword in query_lower for keyword in modification_keywords)
            
            if not is_modification:
                # Regular analysis - no modification
                return {"is_modification": False, "analysis": None}
            
            # User wants to modify table(s)
            logger.info(f"🔄 TABLE MODIFICATION detected")
            
            # Prepare context for modification
            context_parts = []
            context_parts.append(f"📊 TABLE MODIFICATION REQUEST")
            context_parts.append(f"USER REQUEST: {query}")
            
            if page_number:
                context_parts.append(f"TARGET PAGE: {page_number}")
            
            context_parts.append(f"\nAVAILABLE TABLES:")
            
            for i, table in enumerate(tables, 1):
                context_parts.append(f"\n--- TABLE {i}: {table['title']} ---")
                context_parts.append(f"Structure: {table['row_count']} rows × {table['column_count']} columns")
                context_parts.append(f"Current Data:")
                context_parts.append(table['markdown_content'])
            
            context = "\n".join(context_parts)
            
            # 🎯 SPECIALIZED TABLE MODIFICATION PROMPT
            modification_prompt = f"""🎯 INTELLIGENT TABLE MODIFICATION SYSTEM

{context}

MISSION: Execute the user's table modification request with precision.

MODIFICATION CAPABILITIES:
1. 📝 DATA CHANGES: Modify existing values, add/remove rows/columns
2. 🔢 CALCULATIONS: Perform mathematical operations on data
3. 🎨 FORMATTING: Restructure table layout, headers, organization
4. ➕ ADDITIONS: Add new data, columns, or computed fields
5. ❌ DELETIONS: Remove specific rows, columns, or data points
6. 🔄 TRANSFORMATIONS: Convert data formats, create summaries

RESPONSE REQUIREMENTS:
1. **MODIFICATION SUMMARY**: Clearly describe what changes you're making
2. **NEW TABLE**: Provide the complete modified table in perfect markdown format
3. **CHANGE LOG**: List all specific modifications made
4. **DOWNLOAD INFO**: Confirm the table is ready for download

RESPONSE FORMAT:
🔄 TABLE MODIFICATION COMPLETED

Modification Summary:
[Describe exactly what was changed and why]

Modified Table:
[Complete new table in perfect markdown format]

Change Log:

[Specific change 1]

[Specific change 2]

[etc.]

Download Ready: ✅ Your modified table is ready for download as markdown file.

text

IMPORTANT RULES:
- Create a COMPLETE new table with ALL data (don't truncate)
- Use proper markdown table formatting
- Maintain data integrity while implementing changes
- If user request is unclear, make reasonable assumptions and explain them

EXECUTE MODIFICATION NOW:"""
            
            # Generate modification
            response = self.llm_text.generate_content(modification_prompt)
            modification_result = response.text
            
            # 1. Extract the clean Markdown table from the full text response.
            new_table_md = self._extract_table_from_response(modification_result)
            if not new_table_md:
                # If extraction fails, return the full text but flag it.
                logger.error("Failed to extract Markdown table from LLM response.")
                return {"is_modification": False, "analysis_text": "I tried to modify the table, but there was a formatting error."}

            # 2. Extract the summary text (everything EXCEPT the table).
            analysis_text = modification_result.replace(new_table_md, "").strip()

            # 3. Generate a unique ID for the download.
            download_id = hashlib.md5(f"{query}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]

            # 4. Return a structured dictionary for the API layer to use.
            return {
                "is_modification": True,
                "analysis_text": analysis_text,          # The human-readable summary.
                "modified_table_markdown": new_table_md, # The pure, clean Markdown table.
                "download_id": download_id,
                "download_ready": True,
            }
            
        except Exception as e:
            logger.error(f"Error in table modification: {e}", exc_info=True)
            return { "is_modification": False, "analysis_text": f"Failed to modify table: {str(e)}" }
        


    
    def _extract_table_from_response(self, response: str) -> Optional[str]:
        """Extract markdown table from LLM response using regex for better accuracy."""
        try:
            # This regex looks for a block that starts with "Modified Table:"
            # and captures everything until the next major section like "Change Log:" or end of string.
            match = re.search(r"Modified Table:\n(.+?)(?=\n\n\w+|\Z)", response, re.DOTALL)
            if match:
                table_md = match.group(1).strip()
                # Further clean up just in case
                table_lines = [line.strip() for line in table_md.split('\n') if '|' in line]
                return '\n'.join(table_lines)
            
            # Fallback for simpler cases if regex fails
            lines = response.split('\n')
            table_lines = [line for line in lines if line.strip().startswith('|')]
            if table_lines:
                return '\n'.join(table_lines)

            return None
        except Exception as e:
            logger.error(f"Error extracting table: {e}")
            return None
        
    
    async def _generate_analytical_response(self, tables_data: List[Dict], query: str, page_number: Optional[int], analysis_method: str) -> str:
        """📈 Generate comprehensive analytical response"""
        try:
            # Build context
            context_parts = []
            context_parts.append(f"📊 ANALYTICAL QUERY: {query}")
            
            if page_number:
                context_parts.append(f"🎯 FOCUS: Page {page_number} Analysis")
            else:
                context_parts.append(f"🎯 SCOPE: Complete Document Analysis")
            
            context_parts.append(f"\n📋 AVAILABLE TABLES ({len(tables_data)} total):")
            
            for i, table in enumerate(tables_data, 1):
                context_parts.append(f"\n--- TABLE {i}: {table['title']} ---")
                context_parts.append(f"Location: Page {table['start_page']}")
                if table['start_page'] != table['end_page']:
                    context_parts.append(f"Spans to: Page {table['end_page']}")
                context_parts.append(f"Structure: {table['row_count']} rows × {table['column_count']} columns")
                context_parts.append(f"Data:")
                context_parts.append(table['markdown_content'])
            
            context = "\n".join(context_parts)
            
            # 🎯 SPECIALIZED ANALYTICAL PROMPT
            analytical_prompt = f"""🎯 EXPERT ANALYTICAL ASSISTANT

{context}

MISSION: Provide comprehensive analytical insights based on the table data.

ANALYTICAL CAPABILITIES:
1. 📊 DATA ANALYSIS: Extract patterns, trends, correlations
2. 🔢 CALCULATIONS: Perform mathematical operations, statistics
3. 📈 TRENDS: Identify growth, decline, seasonal patterns
4. 🔍 COMPARISONS: Compare values, categories, time periods
5. 💡 INSIGHTS: Generate business intelligence and recommendations
6. 📋 SUMMARIES: Create executive summaries of key findings

RESPONSE STRUCTURE:
📊 **ANALYTICAL INSIGHTS**

**Key Findings:**
[Bullet point list of main discoveries]

**Data Analysis:**
[Detailed examination of the data with specific numbers and percentages]

**Trends & Patterns:**
[Identify any trends, patterns, or anomalies in the data]

**Calculations & Statistics:**
[Relevant calculations, averages, totals, growth rates, etc.]

**Comparative Analysis:**
[Compare different data points, categories, or time periods]

**Business Insights:**
[Strategic insights and recommendations based on the data]

**Summary:**
[Concise summary of the most important analytical conclusions]

ANALYTICAL GUIDELINES:
- Use specific numbers and percentages from the data
- Identify the most significant insights
- Provide actionable recommendations when relevant
- Be precise and data-driven in your analysis
- Cite specific table data to support your conclusions

EXECUTE ANALYSIS NOW:"""
            
            # Generate response
            response = self.llm_text.generate_content(analytical_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating analytical response: {e}")
            return f"I encountered an error while analyzing the data: {str(e)}"
    
    async def _create_image_chunk_parallel(self, image, document_filename: str, document_id: str) -> Optional[DocumentChunk]:
        """🚀 PARALLEL: Create image chunk with ultra-fast analysis"""
        try:
            analysis = await self._analyze_cloudinary_image_ultra_fast(image.cloudinary_url)
            
            image_context = f"""🖼️ PAGE {image.page_number} IMAGE:

URL: {image.cloudinary_url}

ANALYSIS:
{analysis}

Visual content from page {image.page_number}."""
            
            # ✅ PARALLEL EMBEDDING: Run in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.thread_pool,
                self.embedding_model.encode,
                image_context
            )
            
            return DocumentChunk(
                document_id=document_id,
                page_number=image.page_number,
                chunk_index=0,
                content_type='image',
                content=image_context,
                embedding=embedding.tolist(),
                metadata={
                    'filename': document_filename,
                    'source': 'ultra_parallel_analysis',
                    'cloudinary_url': image.cloudinary_url,
                    'phase': 'ultra_parallel'
                }
            )
            
        except Exception as e:
            logger.error(f"Error in parallel chunk creation {image.cloudinary_url}: {e}")
            return None
    
    # ✅ GET CACHED IMAGE ANALYSIS
    async def _get_cached_image_analyses(self, document_id: str) -> Dict[str, Any]:
        """🚀 Get pre-analyzed image data from chunks"""
        try:
            image_chunks = await DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "image"
            ).to_list()
            
            cached_analyses = {}
            
            for chunk in image_chunks:
                page_num = chunk.page_number
                if page_num not in cached_analyses:
                    cached_analyses[page_num] = []
                
                cloudinary_url = chunk.metadata.get('cloudinary_url', '')
                
                cached_analyses[page_num].append({
                    'url': cloudinary_url,
                    'analysis': chunk.content,
                    'page_number': page_num
                })
            
            logger.info(f"📋 Retrieved cached analysis for {len(image_chunks)} images")
            return cached_analyses
            
        except Exception as e:
            logger.error(f"Error getting cached image analyses: {e}")
            return {}
    
    # ✅ GET DOCUMENT CONTENT EFFICIENTLY
    async def _get_complete_document_content_efficiently(self, document_id: str) -> Dict[str, Any]:
        """🚀 Get document content using cached analysis"""
        try:
            content_data = await self._get_complete_document_content(document_id)
            
            if 'error' in content_data:
                return content_data
            
            # Get cached image analyses
            cached_image_analyses = await self._get_cached_image_analyses(document_id)
            
            content_data['image_analyses'] = cached_image_analyses
            content_data['total_images_analyzed'] = sum(len(analyses) for analyses in cached_image_analyses.values())
            
            return content_data
            
        except Exception as e:
            logger.error(f"Error getting document content efficiently: {e}")
            return {"error": str(e)}
    
    async def _get_complete_document_content(self, document_id: str) -> Dict[str, Any]:
        """✅ Get document content from page-wise chunks"""
        try:
            # Get document info
            document = await PDF.get(PyObjectId(document_id))
            if not document:
                return {"error": "Document not found"}
            
            actual_page_count = getattr(document, 'page_count', 1)
            
            # ✅ PARALLEL: Get all data types simultaneously
            text_task = DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "text"
            ).to_list()
            
            images_task = Image.find(Image.pdf_id == PyObjectId(document_id)).to_list()
            tables_task = Table.find(Table.pdf_id == PyObjectId(document_id)).to_list()
            
            # ✅ PARALLEL EXECUTION
            text_chunks, images, tables = await asyncio.gather(text_task, images_task, tables_task)
            
            text_chunks.sort(key=lambda x: x.page_number)
            images.sort(key=lambda x: x.page_number)
            tables.sort(key=lambda x: x.start_page or 1)
            
            complete_text = ""
            page_text_map = {}
            
            for chunk in text_chunks:
                page_num = chunk.page_number
                page_content = chunk.content
                if page_content:
                    complete_text += f"\n--- PAGE {page_num} ---\n{page_content}\n"
                    page_text_map[page_num] = page_content
            
            images_by_page = {}
            for image in images:
                page_num = min(image.page_number, actual_page_count)
                if page_num not in images_by_page:
                    images_by_page[page_num] = []
                images_by_page[page_num].append({
                    'cloudinary_url': image.cloudinary_url,
                    'page_number': page_num
                })
            
            tables_by_page = {}
            for table in tables:
                page_num = min(table.start_page or 1, actual_page_count)
                if page_num not in tables_by_page:
                    tables_by_page[page_num] = []
                tables_by_page[page_num].append({
                    'id': str(table.id),
                    'title': table.table_title,
                    'markdown_content': table.markdown_content,
                    'row_count': table.row_count,
                    'column_count': table.column_count,
                    'page_number': page_num
                })
            
            return {
                'document': document,
                'actual_page_count': actual_page_count,
                'complete_text': complete_text,
                'page_text_map': page_text_map,
                'images_by_page': images_by_page,
                'tables_by_page': tables_by_page,
                'total_images': len(images),
                'total_tables': len(tables)
            }
            
        except Exception as e:
            logger.error(f"Error getting document content: {e}")
            return {"error": str(e)}
    
    # ✅ CHECK DOCUMENT READINESS
    async def _ensure_document_indexed(self, document_id: str) -> bool:
        """✅ Check if document has page-wise text chunks"""
        try:
            text_chunk_count = await DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "text"
            ).count()
            image_count = await Image.find(
                Image.pdf_id == PyObjectId(document_id)
            ).count()
            table_count = await Table.find(
                Table.pdf_id == PyObjectId(document_id)
            ).count()
            
            if text_chunk_count == 0 and image_count == 0 and table_count == 0:
                logger.warning(f"⚠️ Document {document_id} has no page-wise text chunks")
                return False
            else:
                logger.info(f"✅ Document is ready")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error checking document readiness: {e}")
            return False
    
    # 🚀 ULTRA-PARALLEL: CONDITIONAL ANALYSIS
    async def _analyze_relevant_pages_conditionally(self, document_id: str, relevant_pages: set) -> Dict[str, Any]:
        """🚀 ULTRA-PARALLEL: Maximum speed analysis for relevant pages"""
        try:
            logger.info(f"🎯 ULTRA-PARALLEL analysis for pages {sorted(relevant_pages)} in document {document_id}")
            
            document = await PDF.get(PyObjectId(document_id))
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # ✅ PARALLEL: Get existing chunks and images simultaneously
            existing_image_task = DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "image"
            ).to_list()
            
            existing_table_task = DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "table"
            ).to_list()
            
            images_task = Image.find(Image.pdf_id == PyObjectId(document_id)).to_list()
            tables_task = Table.find(Table.pdf_id == PyObjectId(document_id)).to_list()
            
            existing_image_chunks, existing_table_chunks, images, tables = await asyncio.gather(
                existing_image_task, existing_table_task, images_task, tables_task
            )
            
            analyzed_image_pages = set(chunk.page_number for chunk in existing_image_chunks)
            analyzed_table_pages = set(chunk.page_number for chunk in existing_table_chunks)
            
            # 🚀 ULTRA-PARALLEL: Process ALL images simultaneously
            images_to_analyze = [
                image for image in images 
                if image.page_number in relevant_pages and image.page_number not in analyzed_image_pages
            ]
            
            additional_chunks = []
            
            if images_to_analyze:
                logger.info(f"🚀 ULTRA-PARALLEL processing {len(images_to_analyze)} images SIMULTANEOUSLY")
                
                # ✅ MAXIMUM PARALLELISM: Process ALL images at once
                image_tasks = [
                    self._create_image_chunk_parallel(image, document.filename, document_id)
                    for image in images_to_analyze
                ]
                
                # ✅ ALL IMAGES PROCESSED IN PARALLEL
                image_results = await asyncio.gather(*image_tasks, return_exceptions=True)
                
                image_chunks_created = 0
                for result in image_results:
                    if isinstance(result, DocumentChunk):
                        additional_chunks.append(result)
                        image_chunks_created += 1
                    elif isinstance(result, Exception):
                        logger.error(f"Image processing error: {result}")
                        
                logger.info(f"⚡ ULTRA-PARALLEL image processing complete: {image_chunks_created} images")
            else:
                image_chunks_created = 0
            
            # ✅ PARALLEL TABLE PROCESSING
            table_chunks_created = 0
            table_tasks = []
            
            for table in tables:
                table_page = table.start_page or 1
                if table_page in relevant_pages and table_page not in analyzed_table_pages and table.markdown_content:
                    table_tasks.append(self._create_table_chunk_parallel(table, document.filename, document_id))
            
            if table_tasks:
                table_results = await asyncio.gather(*table_tasks, return_exceptions=True)
                for result in table_results:
                    if isinstance(result, DocumentChunk):
                        additional_chunks.append(result)
                        table_chunks_created += 1
            
            # ✅ BATCH INSERT ALL CHUNKS
            if additional_chunks:
                await DocumentChunk.insert_many(additional_chunks)
                logger.info(f"✅ ULTRA-PARALLEL Analysis: {image_chunks_created} images + {table_chunks_created} tables")
            
            return {
                "success": True,
                "image_chunks_created": image_chunks_created,
                "table_chunks_created": table_chunks_created,
                "relevant_pages": sorted(relevant_pages),
                "ultra_parallel": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error in ultra-parallel analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_table_chunk_parallel(self, table, document_filename: str, document_id: str) -> Optional[DocumentChunk]:
        """🚀 PARALLEL: Create table chunk"""
        try:
            table_page = table.start_page or 1
            
            table_context = f"""📊 TABLE FROM PAGE {table_page}:

Table: {table.table_title or 'Table'}
Structure: {table.row_count} rows × {table.column_count} columns

TABLE DATA:
{table.markdown_content}

Structured data from page {table_page}."""
            
            # ✅ PARALLEL EMBEDDING
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.thread_pool,
                self.embedding_model.encode,
                table_context
            )
            
            return DocumentChunk(
                document_id=document_id,
                page_number=table_page,
                chunk_index=0,
                content_type='table',
                content=table_context,
                embedding=embedding.tolist(),
                metadata={
                    'filename': document_filename,
                    'source': 'ultra_parallel_table',
                    'table_title': table.table_title,
                    'phase': 'ultra_parallel'
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating table chunk: {e}")
            return None
    
    # ✅ ULTRA-PARALLEL FALLBACK
    async def _analyze_document_images_and_tables(self, document_id: str) -> Dict[str, Any]:
        """✅ ULTRA-PARALLEL FALLBACK: Analyze all remaining content"""
        try:
            logger.info(f"🔄 ULTRA-PARALLEL fallback for document {document_id}")
            
            document = await PDF.get(PyObjectId(document_id))
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # ✅ PARALLEL: Get all data simultaneously
            text_chunks_task = DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "text"
            ).to_list()
            
            existing_image_task = DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "image"
            ).to_list()
            
            existing_table_task = DocumentChunk.find(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content_type == "table"
            ).to_list()
            
            images_task = Image.find(Image.pdf_id == PyObjectId(document_id)).to_list()
            tables_task = Table.find(Table.pdf_id == PyObjectId(document_id)).to_list()
            
            text_chunks, existing_image_chunks, existing_table_chunks, images, tables = await asyncio.gather(
                text_chunks_task, existing_image_task, existing_table_task, images_task, tables_task
            )
            
            existing_pages = set(chunk.page_number for chunk in text_chunks)
            analyzed_image_pages = set(chunk.page_number for chunk in existing_image_chunks)
            analyzed_table_pages = set(chunk.page_number for chunk in existing_table_chunks)
            
            # 🚀 ULTRA-PARALLEL: Process ALL remaining images
            images_to_analyze = [
                image for image in images 
                if image.page_number in existing_pages and image.page_number not in analyzed_image_pages
            ]
            
            additional_chunks = []
            
            if images_to_analyze:
                logger.info(f"🚀 ULTRA-PARALLEL fallback: {len(images_to_analyze)} images SIMULTANEOUSLY")
                
                image_tasks = [
                    self._create_image_chunk_parallel(image, document.filename, document_id)
                    for image in images_to_analyze
                ]
                
                image_results = await asyncio.gather(*image_tasks, return_exceptions=True)
                
                image_chunks_created = 0
                for result in image_results:
                    if isinstance(result, DocumentChunk):
                        additional_chunks.append(result)
                        image_chunks_created += 1
            else:
                image_chunks_created = 0
            
            # ✅ PARALLEL TABLE PROCESSING
            tables_to_analyze = [
                table for table in tables
                if (table.start_page or 1) in existing_pages 
                and (table.start_page or 1) not in analyzed_table_pages 
                and table.markdown_content
            ]
            
            if tables_to_analyze:
                table_tasks = [
                    self._create_table_chunk_parallel(table, document.filename, document_id)
                    for table in tables_to_analyze
                ]
                
                table_results = await asyncio.gather(*table_tasks, return_exceptions=True)
                
                table_chunks_created = 0
                for result in table_results:
                    if isinstance(result, DocumentChunk):
                        additional_chunks.append(result)
                        table_chunks_created += 1
            else:
                table_chunks_created = 0
            
            # ✅ BATCH INSERT
            if additional_chunks:
                await DocumentChunk.insert_many(additional_chunks)
                logger.info(f"✅ ULTRA-PARALLEL Fallback: {image_chunks_created} images + {table_chunks_created} tables")
                
                return {
                    "success": True,
                    "image_chunks_created": image_chunks_created,
                    "table_chunks_created": table_chunks_created,
                    "total_additional_chunks": len(additional_chunks),
                    "ultra_parallel": True
                }
            else:
                return {"success": True, "message": "No additional content to analyze"}
                
        except Exception as e:
            logger.error(f"❌ Error in ultra-parallel fallback: {e}")
            return {"success": False, "error": str(e)}
    
    # ✅ CHAT SESSION MANAGEMENT
    async def start_new_chat_session(self, 
                                   user_id: str, 
                                   chat_type: ChatType,
                                   document_id: Optional[str] = None,
                                   title: Optional[str] = None) -> Dict[str, Any]:
        """🆕 START NEW CHAT SESSION (instant)"""
        try:
            if document_id:
                indexed = await self._ensure_document_indexed(document_id)
                if not indexed:
                    return {
                        "success": False,
                        "error": "Document not ready - missing page-wise chunks",
                        "message": "Please ensure Phase 1 processing is complete."
                    }
            
            session_id = f"{user_id}_{chat_type.value}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            if not title:
                if document_id:
                    document = await PDF.get(PyObjectId(document_id))
                    doc_name = document.filename if document else "Document"
                    title = f"{chat_type.value.title()} Chat - {doc_name}"
                else:
                    title = f"{chat_type.value.title()} Chat"
            
            session = ChatSession(
                session_id=session_id,
                user_id=PyObjectId(user_id),
                document_id=PyObjectId(document_id) if document_id else None,
                chat_type=chat_type,
                title=title,
                description=f"New {chat_type.value} chat session"
            )
            await session.insert()
            
            logger.info(f"🆕 Created {chat_type.value} session: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "chat_type": chat_type.value,
                "title": title,
                "document_id": document_id,
                "created_at": session.created_at.isoformat(),
                "message": f"New {chat_type.value} chat session started"
            }
            
        except Exception as e:
            logger.error(f"Error starting chat session: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_chat_sessions(self, 
                                   user_id: str, 
                                   chat_type: Optional[ChatType] = None,
                                   document_id: Optional[str] = None,
                                   limit: int = 20) -> Dict[str, Any]:
        """📋 GET USER'S CHAT SESSIONS"""
        try:
            query = {"user_id": PyObjectId(user_id), "is_active": True}
            
            if chat_type:
                query["chat_type"] = chat_type
            if document_id:
                query["document_id"] = PyObjectId(document_id)
            
            sessions = await ChatSession.find(query).sort(-ChatSession.updated_at).limit(limit).to_list()
            
            session_list = []
            for session in sessions:
                session_list.append({
                    "session_id": session.session_id,
                    "chat_type": session.chat_type,
                    "title": session.title,
                    "description": session.description,
                    "document_id": str(session.document_id) if session.document_id else None,
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "last_activity": session.last_activity.isoformat()
                })
            
            return {"success": True, "sessions": session_list, "total_sessions": len(session_list)}
            
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return {"success": False, "error": str(e)}
    
    # ✅ MESSAGE HANDLER
        # ✅ MESSAGE HANDLER (UPDATE THIS PART)
    async def send_message(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
        """💬 SEND MESSAGE"""
        try:
            # ✅ IMPORTANT: Get session first
            session = await ChatSession.find_one(ChatSession.session_id == session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if str(session.user_id) != user_id:
                return {"success": False, "error": "Access denied"}
            
            # Route to chat handlers - PASS session object
            if session.chat_type == ChatType.GENERAL:
                return await self._handle_general_chat(session, message, user_id)
            elif session.chat_type == ChatType.ANALYTICAL:
                return await self._handle_enhanced_analytical_chat(session, message, user_id) 
            else:
                return {"success": False, "error": f"Unknown chat type: {session.chat_type}"}
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"success": False, "error": str(e), "response": "I encountered an error."}


    
    # ✅ ULTRA-FAST GENERAL CHAT
    async def _handle_general_chat(self, session: ChatSession, message: str, user_id: str) -> Dict[str, Any]:
        """💬 ULTRA-FAST: General chat with maximum parallel processing"""
        try:
            # Save user message
            user_message = ChatMessage(
                session_id=session.session_id,
                user_id=PyObjectId(user_id),
                document_id=session.document_id,
                chat_type=ChatType.GENERAL,
                role="user",
                content=message
            )
            await user_message.insert()
            
            # ✅ PARALLEL: Get chat history and process query simultaneously
            history_task = ChatMessage.find(
                ChatMessage.session_id == session.session_id
            ).sort(-ChatMessage.timestamp).limit(10).to_list()
            
            if session.document_id:
                # ✅ PARALLEL: Find relevant chunks
                loop = asyncio.get_event_loop()
                query_embedding_task = loop.run_in_executor(
                    self.thread_pool,
                    self.embedding_model.encode,
                    [message]
                )
                
                recent_messages, query_embedding = await asyncio.gather(history_task, query_embedding_task)
                recent_messages.reverse()
                
                relevant_chunks = await self._search_chunks(str(session.document_id), query_embedding[0].tolist(), limit=8)
                
                if relevant_chunks:
                    relevant_pages = set(chunk.page_number for chunk in relevant_chunks)
                    logger.info(f"🎯 Relevant pages: {sorted(relevant_pages)}")
                    
                    # 🚀 ULTRA-PARALLEL: Analysis
                    await self._analyze_relevant_pages_conditionally(str(session.document_id), relevant_pages)
                else:
                    logger.info(f"🔍 No specific pages - analyzing all")
                    await self._analyze_document_images_and_tables(str(session.document_id))
                
                # Get content
                content_data = await self._get_complete_document_content_efficiently(str(session.document_id))
                
                if 'error' in content_data:
                    response_text = f"Error accessing document: {content_data['error']}"
                else:
                    # Build context
                    context_parts = [
                        f"DOCUMENT: {content_data['document'].filename}",
                        f"USER QUESTION: {message}"
                    ]
                    
                    # Add history
                    if len(recent_messages) > 1:
                        context_parts.append("\nRECENT CONVERSATION:")
                        for msg in recent_messages[-6:-1]:
                            context_parts.append(f"{msg.role.upper()}: {msg.content}")
                    
                    # Add relevant chunks
                    if relevant_chunks:
                        context_parts.append("\nRELEVANT CONTENT:")
                        for chunk in relevant_chunks[:4]:
                            context_parts.append(f"\n--- {chunk.content_type.upper()} FROM PAGE {chunk.page_number} ---")
                            context_parts.append(chunk.content)
                    
                    # Add image analyses
                    image_analyses = content_data.get('image_analyses', {})
                    images_analyzed = []
                    
                    if image_analyses:
                        context_parts.append("\n🖼️ IMAGE ANALYSES:")
                        for page_num, analyses in image_analyses.items():
                            for analysis in analyses:
                                context_parts.append(f"\n--- 🖼️ PAGE {page_num} IMAGE ---")
                                context_parts.append(f"URL: {analysis['url']}")
                                context_parts.append(f"Analysis: {analysis['analysis']}")
                                images_analyzed.append(analysis['url'])
                    
                    # Add complete text
                    if content_data.get('complete_text'):
                        context_parts.append(f"\nCOMPLETE DOCUMENT TEXT:")
                        context_parts.append(content_data['complete_text'])
                    
                    context = "\n".join(context_parts)
                    
                    system_prompt = """You are a helpful assistant

GUIDELINES:
1. Base answers on provided content (text + images + tables)
2. Describe images based on analysis provided
3. Always cite page numbers
4. Be detailed and thorough
5. Combine all information sources
6. If you do not find relevant answer based on the context, then inform the user that it is not in the context and give a correct answer by yourself
"""

                    full_prompt = f"""{system_prompt}

{context}

Question: {message}

Provide comprehensive answer using all available content and your intelligence:"""
                    
                    # Generate response
                    try:
                        response = self.llm_text.generate_content(full_prompt)
                        response_text = response.text
                    except Exception as e:
                        logger.error(f"Response generation error: {e}")
                        response_text = "Error generating response. Please try again."
                    
                    # Save response
                    assistant_message = ChatMessage(
                        session_id=session.session_id,
                        user_id=PyObjectId(user_id),
                        document_id=session.document_id,
                        chat_type=ChatType.GENERAL,
                        role="assistant",
                        content=response_text,
                        images_analyzed=images_analyzed,
                        metadata={
                            "relevant_chunks": len(relevant_chunks),
                            "images_analyzed": len(images_analyzed),
                            "ultra_parallel": True,
                            "relevant_pages": sorted(relevant_pages) if 'relevant_pages' in locals() else []
                        }
                    )
                    await assistant_message.insert()
            else:
                # ✅ FIXED: Standalone chat with memory
                recent_messages = await history_task
                recent_messages.reverse()
    
             # ✅ BUILD PROMPT WITH HISTORY
                if len(recent_messages) > 1:
                    conversation_history = "\nRECENT CONVERSATION:\n"
                    for msg in recent_messages[-6:-1]:  # Last 5 messages
                        conversation_history += f"{msg.role.upper()}: {msg.content}\n"
        
                    prompt = f"""You are a helpful AI assistant with conversation memory.

            {conversation_history}

            CURRENT MESSAGE: {message}

            Remember previous conversations and provide a helpful response:"""
                else:
                    prompt = f"User: {message}\n\nProvide helpful response:"

                
                try:
                    response = self.llm_text.generate_content(f"User: {prompt}\n\nProvide helpful response:")
                    response_text = response.text
                except Exception as e:
                    response_text = "Error occurred. Please try again."
                
                assistant_message = ChatMessage(
                    session_id=session.session_id,
                    user_id=PyObjectId(user_id),
                    chat_type=ChatType.GENERAL,
                    role="assistant",
                    content=response_text
                )
                await assistant_message.insert()
            
            # Update session
            session.updated_at = datetime.now()
            session.last_activity = datetime.now()
            session.message_count += 2
            await session.save()
            
            return {
                "success": True,
                "response": response_text,
                "metadata": {
                    "session_id": session.session_id,
                    "chat_type": "general",
                    "message_count": session.message_count,
                    "images_analyzed": len(images_analyzed) if 'images_analyzed' in locals() else 0,
                    "ultra_parallel": True,
                    "document_id": str(session.document_id) if session.document_id else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in general chat: {e}")
            return {"success": False, "error": str(e), "response": "Error processing message."}
    
    # 🎯 ENHANCED ANALYTICAL CHAT HANDLER (MAIN FEATURE)
    async def _handle_enhanced_analytical_chat(self, session: ChatSession, message: str, user_id: str) -> Dict[str, Any]:
        """🎯 ENHANCED: Analytical chat with optimized conversation memory"""
        try:
            # Save user message
            user_message = ChatMessage(
                session_id=session.session_id, user_id=PyObjectId(user_id),
                document_id=session.document_id, chat_type=ChatType.ANALYTICAL,
                role="user", content=message
            )
            await user_message.insert()
            
            # This call fetches the recent conversation history as a formatted string.
            chat_history = await self._get_optimized_analytical_history(session.session_id)
            
            if not session.document_id:
                response_text = "🚫 Analytical chat requires a document with tables. Please upload a document containing structured data."
                # ... (rest of no-document handling logic)
                return { "success": True, "response": response_text }

            page_number, clean_query = self._extract_page_number_from_query(message)
            
            # Logic to get tables (your existing code is correct)
            if page_number:
                tables_data = await self._get_page_tables(str(session.document_id), page_number)
            else:
                all_tables = await Table.find(Table.pdf_id == PyObjectId(session.document_id)).to_list()
                tables_data = [{'id': str(t.id), 'title': t.table_title, 'markdown_content': t.markdown_content, 'row_count': t.row_count, 'column_count': t.column_count, 'start_page': t.start_page, 'end_page': t.end_page} for t in all_tables]

            response_payload = {}
            # Check for modification intent
            modification_keywords = ['change', 'modify', 'update', 'edit', 'add', 'remove', 'delete', 'replace']
            if any(keyword in message.lower() for keyword in modification_keywords) and tables_data:
                # This is a modification request
                modification_result = await self._handle_table_modification(tables_data, message, page_number)
                
                # ✅ THE FIX: Construct the final response payload from the structured result.
                if modification_result.get("is_modification"):
                    response_payload = {
                        "success": True,
                        # Combine the summary and the table for display in the chat.
                        "response": f"{modification_result['analysis_text']}\n\n{modification_result['modified_table_markdown']}",
                        "metadata": {
                            "chat_type": "analytical",
                            "response_type": "table_modification", # New flag for the frontend
                            "is_modification": True,
                            "download_ready": True,
                            "show_download_button": True, # New flag for the frontend
                            "download_id": modification_result['download_id'],
                            "new_table_markdown": modification_result['modified_table_markdown'], # Pass clean MD for storage
                        }
                    }
                else:
                    response_payload = {"success": True, "response": modification_result.get("analysis_text", "An error occurred."), "metadata": {}}
            else:
                # Regular analysis
                if not tables_data:
                    # Fallback to image analysis
                    response_text = await self._analyze_page_image_for_tables(str(session.document_id), page_number, message) if page_number else "No tables found to analyze."
                else:
                    chat_history = await self._get_optimized_analytical_history(session.session_id)
                    response_text = await self._generate_analytical_response_with_history(tables_data, message, page_number, chat_history)
                response_payload = {"success": True, "response": response_text, "metadata": {"chat_type": "analytical"}}

            # Save assistant message
            assistant_message = ChatMessage(
                session_id=session.session_id, user_id=PyObjectId(user_id),
                document_id=session.document_id, chat_type=ChatType.ANALYTICAL,
                role="assistant", content=response_payload['response'],
                metadata=response_payload.get('metadata') # Save the rich metadata
            )
            await assistant_message.insert()

            # Update session
            session.updated_at = datetime.now()
            session.last_activity = datetime.now()
            session.message_count += 2
            await session.save()

            return response_payload

        except Exception as e:
            logger.error(f"Error in enhanced analytical chat: {e}", exc_info=True)
            return {"success": False, "error": str(e), "response": "I encountered an error processing your analytical request."}
        

        

    # -------------------------------------------------------------------------
    # ✅ NEW: IMPLEMENTATION OF THE MISSING FUNCTION
    # -------------------------------------------------------------------------
    async def _generate_analytical_response_with_history(self, tables_data: List[Dict], query: str, page_number: Optional[int], chat_history: str) -> str:
        """📈 Generate comprehensive analytical response, now with conversation history."""
        try:
            # Build context
            context_parts = []
            context_parts.append(f"You are an expert financial and data analyst. Your task is to analyze the provided table data in the context of the ongoing conversation.")
            
            # Add conversation history to the prompt
            if chat_history:
                context_parts.append("\n--- CONVERSATION HISTORY (for context) ---")
                context_parts.append(chat_history)
                context_parts.append("--- END OF HISTORY ---")

            context_parts.append(f"\nCURRENT USER REQUEST: \"{query}\"")
            
            if page_number:
                context_parts.append(f"🎯 FOCUS: The user is asking about data on Page {page_number}.")
            else:
                context_parts.append(f"🎯 SCOPE: The user is asking about the entire document.")
            
            context_parts.append(f"\n📋 AVAILABLE DATA:")
            for i, table in enumerate(tables_data, 1):
                context_parts.append(f"\n--- TABLE {i}: {table.get('title', 'Untitled')} (from Page {table.get('start_page', 'N/A')}) ---")
                context_parts.append(table.get('markdown_content', 'No content available.'))
            
            context = "\n".join(context_parts)
            
            # Specialized analytical prompt that now incorporates history
            analytical_prompt = f"""{context}

MISSION: Based on the conversation history and the user's current request, provide a comprehensive analytical response using the available table data.

RESPONSE GUIDELINES:
- **Do not Acknowledge History**: Just take it in context but do not repeat it.
- **Answer the Current Request**: Your primary focus is to answer the user's *current* request.
- **Be Data-Driven**: Ground your entire analysis in the provided table data.
- **Cite Sources**: Mention which table or page your analysis comes from.
- **Provide Insights**: Go beyond just restating data; identify trends, perform calculations, and generate key takeaways.

EXECUTE ANALYSIS NOW:"""
            
            response = await self.llm_text.generate_content_async(analytical_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating analytical response with history: {e}", exc_info=True)
            return f"I encountered an error while analyzing the data with conversation history: {str(e)}"

    
  
    
    # ✅ SEARCH UTILITY
    async def _search_chunks(self, document_id: str, query_embedding: List[float], limit: int = 8) -> List[DocumentChunk]:
        """Search chunks with similarity"""
        try:
            chunks = await DocumentChunk.find(DocumentChunk.document_id == document_id).to_list()
            if not chunks:
                return []
            
            # ✅ PARALLEL SIMILARITY CALCULATION
            def calculate_similarity(chunk):
                try:
                    return 1 - cosine(query_embedding, chunk.embedding), chunk
                except:
                    return 0.0, chunk
            
            loop = asyncio.get_event_loop()
            similarity_tasks = [
                loop.run_in_executor(self.thread_pool, calculate_similarity, chunk)
                for chunk in chunks
            ]
            
            similarity_results = await asyncio.gather(*similarity_tasks)
            
            # Sort and filter
            similarity_results.sort(key=lambda x: x[0], reverse=True)
            relevant_chunks = [chunk for score, chunk in similarity_results if score > 0.0]
            
            return relevant_chunks[:limit]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
        
    async def _get_optimized_analytical_history(self, session_id: str, max_messages: int = 10, max_tokens: int = 2000) -> str:
        """
        Retrieves and formats a token-limited chat history for analytical context.
        It prioritizes the most recent messages to maintain conversational flow.
        """
        try:
            messages = await ChatMessage.find(
                ChatMessage.session_id == session_id
            ).sort(-ChatMessage.timestamp).limit(max_messages * 2).to_list() # Fetch a bit more to have room for filtering

            history_context = []
            current_tokens = 0
            
            # Iterate from newest to oldest to build the context
            for msg in messages:
                # A simple token estimation
                msg_tokens = len(msg.content.split())
                
                if current_tokens + msg_tokens > max_tokens:
                    break
                
                history_context.append(f"{msg.role.upper()}: {msg.content}")
                current_tokens += msg_tokens

            # Reverse the list to restore chronological order
            history_context.reverse()
            
            if not history_context:
                return ""
                
            logger.info(f"🧠 Built optimized history for session {session_id} with {len(history_context)} messages and ~{current_tokens} tokens.")
            return "\n".join(history_context)
            
        except Exception as e:
            logger.error(f"Error getting optimized history for session {session_id}: {e}")
            return "" # Return empty string on error
    

    
    async def index_document_for_general_chat(self, document_id: str) -> Dict[str, Any]:
        """Manual indexing (legacy)"""
        return await self._analyze_document_images_and_tables(document_id)
    
    async def delete_document_chunks(self, document_id: str) -> Dict[str, Any]:
        """Delete all chunks AND chats for a document"""
        try:
            # Delete chunks
            chunks_result = await DocumentChunk.find(DocumentChunk.document_id == document_id).delete()
            
            # ✅ ALSO DELETE RELATED CHATS
            chats_result = await self.delete_document_related_chats(document_id)
            
            logger.info(f"🗑️ Deleted {chunks_result.deleted_count} chunks and {chats_result.get('sessions_deleted', 0)} chat sessions for document {document_id}")
            
            return {
                "success": True,
                "deleted_chunks": chunks_result.deleted_count,
                "deleted_sessions": chats_result.get('sessions_deleted', 0),
                "deleted_messages": chats_result.get('messages_deleted', 0),
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting document data: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }

        
    async def delete_document_related_chats(self, document_id: str) -> Dict[str, Any]:
        """🗑️ Delete all chats related to a specific document"""
        try:
            logger.info(f"🗑️ Deleting all chats for document {document_id}")
            
            # Find all sessions related to this document
            sessions = await ChatSession.find(
                ChatSession.document_id == PyObjectId(document_id)
            ).to_list()
            
            if not sessions:
                return {
                    "success": True,
                    "sessions_deleted": 0,
                    "messages_deleted": 0,
                    "message": "No chat sessions found for this document"
                }
            
            session_ids = [session.session_id for session in sessions]
            
            # Delete all messages for these sessions
            messages_result = await ChatMessage.find(
                ChatMessage.session_id.in_(session_ids)
            ).delete()
            
            # Delete all sessions
            sessions_result = await ChatSession.find(
                ChatSession.document_id == PyObjectId(document_id)
            ).delete()
            
            logger.info(f"✅ Deleted {sessions_result.deleted_count} sessions and {messages_result.deleted_count} messages")
            
            return {
                "success": True,
                "sessions_deleted": sessions_result.deleted_count,
                "messages_deleted": messages_result.deleted_count,
                "session_ids": session_ids,
                "message": f"Successfully deleted {sessions_result.deleted_count} chat sessions and {messages_result.deleted_count} messages"
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting document chats: {e}")
            return {
                "success": False,
                "error": str(e),
                "sessions_deleted": 0,
                "messages_deleted": 0
            }
        
    
    async def delete_chat_session(self, session_id: str, user_id: str) -> dict:
        """
        Safely deletes a chat session and all its associated messages,
        preventing 500 Internal Server Errors.
        """
        try:
            # Step 1: Find the session to ensure it exists and belongs to the user.
            session_to_delete = await ChatSession.find_one(
                ChatSession.session_id == session_id,
                ChatSession.user_id == PyObjectId(user_id)
            )

            # Step 2: ✅ THE CRITICAL FIX: Check if the session was actually found.
            # If not found, do not proceed. Return a clean 404 error instead of crashing.
            if not session_to_delete:
                logger.warning(f"Delete failed: Session '{session_id}' not found for user '{user_id}'.")
                return {"success": False, "error": "Session not found."}

            # Step 3: If the session exists, delete all associated messages first.
            await ChatMessage.find(ChatMessage.session_id == session_id).delete()
            
            # Step 4: Now, delete the session object itself.
            await session_to_delete.delete()
            
            logger.info(f"Successfully deleted session '{session_id}' and its messages.")
            
            # Step 5: Return a success response without trying to access the deleted object.
            return {"success": True, "message": "Session and all associated messages deleted successfully."}

        except Exception as e:
            # This will catch any other unexpected database errors.
            logger.error(f"Error during session deletion '{session_id}': {e}", exc_info=True)
            return {"success": False, "error": "An internal server error occurred during deletion."}
        

    
    
    async def cleanup_document_data(self, document_id: str) -> Dict[str, Any]:
        """🧹 COMPLETE cleanup of document data (chats, chunks, etc.)"""
        try:
            logger.info(f"🧹 Complete cleanup for document {document_id}")
            
            # Delete document chunks
            chunks_result = await self.delete_document_chunks(document_id)
            
            # Delete document chats
            chats_result = await self.delete_document_related_chats(document_id)
            
            return {
                "success": True,
                "cleanup_summary": {
                    "chunks_deleted": chunks_result.get("deleted_chunks", 0),
                    "sessions_deleted": chats_result.get("sessions_deleted", 0),
                    "messages_deleted": chats_result.get("messages_deleted", 0)
                },
                "message": "Complete document cleanup successful"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in complete cleanup: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    
    async def get_document_general_chat_info(self, document_id: str) -> Dict[str, Any]:
        """Get document indexing info"""
        try:
            pipeline = [
                {"$match": {"document_id": document_id}},
                {"$group": {"_id": "$content_type", "count": {"$sum": 1}, "pages": {"$addToSet": "$page_number"}}}
            ]
            
            results = await DocumentChunk.aggregate(pipeline).to_list()
            
            chunk_stats = {}
            all_pages = set()
            
            for result in results:
                content_type = result['_id']
                chunk_stats[content_type] = {
                    'count': result['count'],
                    'pages': sorted(result['pages'])
                }
                all_pages.update(result['pages'])
            
            document = await PDF.get(PyObjectId(document_id))
            
            return {
                "indexed": True,
                "total_chunks": sum(stats['count'] for stats in chunk_stats.values()),
                "chunk_breakdown": chunk_stats,
                "text_chunks": chunk_stats.get('text', {}).get('count', 0),
                "image_chunks": chunk_stats.get('image', {}).get('count', 0),
                "table_chunks": chunk_stats.get('table', {}).get('count', 0),
                "pages_indexed": sorted(list(all_pages)),
                "actual_page_count": getattr(document, 'page_count', 1) if document else 1,
                "filename": document.filename if document else None,
                "status": "✅ ENHANCED - Analytical chat with page-specific analysis and table modifications!"
            }
            
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return {"indexed": False, "error": str(e), "status": "❌ Error"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            # ✅ PARALLEL HEALTH CHECK
            embedding_task = asyncio.get_event_loop().run_in_executor(
                self.thread_pool, self.embedding_model.encode, ["test"]
            )
            await embedding_task
            
            return {
                "status": "healthy",
                "embedding_model": "ok",
                "image_analysis": "gemini_1.5_flash_ultra_fast",
                "chat_types": ["general", "analytical"],
                "features": {
                    "enhanced_analytical_chat": True,
                    "page_specific_analysis": True,
                    "table_modifications": True,
                    "image_fallback_analysis": True,
                    "download_functionality": True,
                    "ultra_parallel_processing": True,
                    "thread_pool_executor": True,
                    "conditional_analysis": True,
                    "page_wise_chunking": True,
                    "multimodal_support": True,
                    "vector_search": True,
                    "persistent_chat_history": True,
                    "maximum_speed_optimization": True
                },
                "storage_type": "database",
                "thread_pool_workers": 10,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
    
    # ✅ LEGACY COMPATIBILITY
    async def general_chat_with_document(self, 
                                       query: str, 
                                       document_id: Optional[str] = None,
                                       user_id: str = None,
                                       conversation_id: str = "default") -> Dict[str, Any]:
        """🔄 LEGACY: Backward compatibility"""
        try:
            chat_type = ChatType.GENERAL
            legacy_session_id = f"legacy_{user_id}_{conversation_id}_{document_id if document_id else 'standalone'}"
            
            session = await ChatSession.find_one(ChatSession.session_id == legacy_session_id)
            
            if not session:
                session_result = await self.start_new_chat_session(
                    user_id=user_id,
                    chat_type=chat_type,
                    document_id=document_id,
                    title=f"Legacy General Chat - {conversation_id}"
                )
                if not session_result["success"]:
                    return {"success": False, "error": session_result.get("error", "Failed to create session")}
                session_id = session_result["session_id"]
            else:
                session_id = session.session_id
            
            return await self.send_message(session_id=session_id, user_id=user_id, message=query)
            
        except Exception as e:
            logger.error(f"Error in legacy chat: {e}")
            return {"success": False, "error": str(e), "response": "Error occurred."}
    
    def __del__(self):
        """Cleanup thread pool"""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)

# 📥 TABLE DOWNLOAD SERVICE
class TableDownloadService:
    """📥 Handle table downloads"""
    
    @staticmethod
    def create_download_content(table_markdown: str, download_id: str, query: str) -> Dict[str, Any]:
        """Create downloadable content"""
        try:
            # Create file content
            file_content = f"""# Modified Table Analysis
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Query: {query}
Download ID: {download_id}

## Modified Table Data

{table_markdown}

---
Generated by Enhanced Analytical Chat System
"""
            
            return {
                "success": True,
                "content": file_content,
                "filename": f"modified_table_{download_id}.md",
                "content_type": "text/markdown"
            }
            
        except Exception as e:
            logger.error(f"Error creating download content: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instances
multi_chat_service = MultiChatService()
table_download_service = TableDownloadService()