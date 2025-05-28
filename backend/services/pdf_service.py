import sys
import os
import fitz  # PyMuPDF
import datetime
import re
import time
from pdf2image import convert_from_path
import concurrent.futures
from functools import partial
import multiprocessing
import logging
from typing import List, Dict, Tuple, Optional, Any
from PIL import Image
import queue
import threading
from dotenv import load_dotenv
from google import genai
import pathlib
import json
import tempfile
import shutil
from dataclasses import dataclass
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text

# Import our models and services
from models.user import User
from models.pdf import PDF
from models.page_text import PageText
from models.table import Table
from models.image import Image as ImageModel
from storage_service import storage_service

@dataclass
class TableInfo:
    """Structure for table information from LLM"""
    table_id: int
    title: str
    start_page: int
    end_page: int
    markdown_content: str
    column_headers: List[str]
    row_count: int
    column_count: int

class ApiKeyManager:
    """Manages API keys and client rotation in a thread-safe manner with rate limiting"""
    
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.active_keys_lock = threading.Lock()
        self.idle_keys_queue = queue.Queue()
        
        # Rate limiting - track last request time for each key
        self.last_request_time = {}
        self.request_interval = 0.2  # Minimum time between requests for the same key
        
        # Initialize clients for all keys
        self.clients = {}
        for key in api_keys:
            self.clients[key] = genai.Client(api_key=key)
            self.last_request_time[key] = 0  # Initialize last request time
            
        # Split keys into active and idle based on half of total keys
        active_count = max(1, len(api_keys))
        self.active_keys = {api_keys[i]: None for i in range(active_count)}  # Key -> thread_id mapping
        
        # Put remaining keys in the idle queue
        for i in range(active_count, len(api_keys)):
            self.idle_keys_queue.put(api_keys[i])
    
    def get_client(self, thread_id):
        """Get an available API client for the thread"""
        with self.active_keys_lock:
            # Check if this thread already has a key assigned
            for key, assigned_thread in self.active_keys.items():
                if assigned_thread == thread_id:
                    return self.clients[key], key
            
            # Find an unassigned key
            for key, assigned_thread in self.active_keys.items():
                if assigned_thread is None:
                    self.active_keys[key] = thread_id
                    return self.clients[key], key
            
            # If no available keys in active set, wait for one from the idle queue
            logger = logging.getLogger("PDFProcessor")
            logger.info(f"Thread {thread_id} waiting for an available API key")
            
        # Get key from idle queue (outside the lock to prevent deadlock)
        idle_key = self.idle_keys_queue.get()
        
        # Acquire lock again to update active keys
        with self.active_keys_lock:
            # Find a key to replace in active keys
            for active_key in self.active_keys:
                if self.active_keys[active_key] is None:
                    self.active_keys[active_key] = thread_id
                    self.active_keys[active_key] = idle_key
                    self.idle_keys_queue.put(active_key)
                    return self.clients[idle_key], idle_key
            
            # If no free slot (shouldn't happen), create a new slot
            self.active_keys[idle_key] = thread_id
            return self.clients[idle_key], idle_key
    
    def release_client(self, key, thread_id):
        """Mark a client as not being used by the thread"""
        with self.active_keys_lock:
            if key in self.active_keys and self.active_keys[key] == thread_id:
                self.active_keys[key] = None
                logger = logging.getLogger("PDFProcessor")
                logger.info(f"Thread {thread_id} released API key")
    
    def rotate_key(self, exhausted_key, thread_id):
        """Move exhausted key to idle queue and get a new key"""
        with self.active_keys_lock:
            if exhausted_key in self.active_keys:
                del self.active_keys[exhausted_key]
                
                # Get new key from idle queue
                try:
                    new_key = self.idle_keys_queue.get_nowait()
                    self.active_keys[new_key] = thread_id
                    
                    # Put exhausted key at the end of idle queue
                    self.idle_keys_queue.put(exhausted_key)
                    
                    # Reset the request time for the new key to ensure proper spacing
                    elapsed = time.time() - self.last_request_time.get(new_key, 0)
                    logger = logging.getLogger("PDFProcessor")
                    if elapsed < self.request_interval:
                        logger.info(f"Thread {thread_id} - New key was used recently ({elapsed:.2f}s ago)")
                    
                    logger.info(f"Thread {thread_id} rotated exhausted key with a new one")
                    return self.clients[new_key], new_key
                except queue.Empty:
                    # If no keys available, put the exhausted key back and let it cool down
                    self.active_keys[exhausted_key] = None
                    logger = logging.getLogger("PDFProcessor")
                    logger.warning(f"No idle keys available, keeping exhausted key {exhausted_key}")
                    # Reset last request time to force a delay before reusing
                    self.last_request_time[exhausted_key] = time.time() - (self.request_interval / 2)
                    return self.clients[exhausted_key], exhausted_key
        
        # Should not reach here
        return self.clients[exhausted_key], exhausted_key

class PDFProcessor:
    """
    Enhanced PDF processor that:
    1. Extracts and saves pages as images with proper rotation
    2. Extracts text using multiple fallback methods
    3. Extracts embedded images from the PDF
    4. Handles multi-page tables with LLM-based similarity checking
    5. Stores everything in database via Cloudinary
    6. Cleans up temporary files
    """
    
    def __init__(self, pdf_path: str, user_id: int, db_session: AsyncSession, temp_folder: str = None):
        """
        Initialize the PDF processor.
        
        Args:
            pdf_path (str): Path to the PDF file
            user_id (int): ID of the user uploading the PDF
            db_session (AsyncSession): Database session
            temp_folder (str): Temporary folder for processing (will be cleaned up)
        """
        self.pdf_path = pdf_path
        self.user_id = user_id
        self.db_session = db_session
        self.file_id = os.path.basename(pdf_path).replace(' ', '_').replace('.pdf', '')
        
        # Set up temporary folder
        if temp_folder is None:
            self.temp_folder = tempfile.mkdtemp(prefix=f"pdf_processing_{self.file_id}_")
        else:
            self.temp_folder = temp_folder
            
        # Create the folder if it doesn't exist
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)
            
        # Set up logger
        self.logger = logging.getLogger("PDFProcessor")
        # Remove all existing handlers to prevent duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        # Add a new handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load Gemini API keys
        load_dotenv()
        self.api_keys = os.getenv("GEMINI_KEYS", "").split(" ")
        if not self.api_keys or self.api_keys == [""]:
            self.logger.warning("No GEMINI_KEYS found in environment variables. Table extraction will be disabled.")
            self.table_extraction_enabled = False
        else:
            self.table_extraction_enabled = True
            
        # Store for multi-page table tracking
        self.processed_tables: List[TableInfo] = []
        
        # PDF database record
        self.pdf_record: Optional[PDF] = None
    
    async def process_pdf(self, filename: str, num_workers: int = 4) -> Dict[str, Any]:
        """
        Process a PDF file and store everything in database.
        
        Args:
            filename (str): Original filename of the PDF
            num_workers (int): Number of worker threads to use
            
        Returns:
            Dict[str, Any]: Processing results and database record info
        """
        start_time = time.time()
        
        try:
            # Check if the PDF file exists
            if not os.path.exists(self.pdf_path):
                self.logger.error(f"Error: The file {self.pdf_path} does not exist.")
                return {"success": False, "error": "File not found"}
            
            # Step 1: Upload PDF to Cloudinary
            with open(self.pdf_path, 'rb') as pdf_file:
                upload_result = await storage_service.upload_document(
                    file=pdf_file,
                    folder="user_documents",
                    public_id=f"user_{self.user_id}_{self.file_id}"
                )
            
            # Step 2: Create PDF record in database
            doc = fitz.open(self.pdf_path)
            num_pages = len(doc)
            doc.close()
            
            self.pdf_record = PDF(
                user_id=self.user_id,
                filename=filename,
                cloudinary_url=upload_result["url"],
                page_count=num_pages,
                processing_status="processing"
            )
            
            self.db_session.add(self.pdf_record)
            await self.db_session.commit()
            await self.db_session.refresh(self.pdf_record)
            
            self.logger.info(f"Created PDF record with ID: {self.pdf_record.id}")
            
            # Step 3: Process pages in parallel
            self.logger.info(f"PDF has {num_pages} pages. Processing using {num_workers} workers")
            
            # Create temporary folders
            page_images_folder = os.path.join(self.temp_folder, "page_images")
            embedded_images_folder = os.path.join(self.temp_folder, "embedded_images")
            os.makedirs(page_images_folder, exist_ok=True)
            os.makedirs(embedded_images_folder, exist_ok=True)
            
            # Process pages in batches
            page_nums = list(range(num_pages))
            cpu_count = min(8, num_workers)
            batch_size = max(1, len(page_nums) // cpu_count)
            page_batches = [page_nums[i:i + batch_size] for i in range(0, len(page_nums), batch_size)]
            
            all_results = []
            
            # Process batches in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
                futures = {
                    executor.submit(self._process_page_batch, batch, page_images_folder, embedded_images_folder): batch 
                    for batch in page_batches
                }
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        batch_results = future.result()
                        all_results.extend(batch_results)
                    except Exception as e:
                        batch = futures[future]
                        self.logger.error(f"Error processing batch {batch}: {str(e)}")
            
            # Sort results by page number
            all_results.sort(key=lambda x: x["page"])
            
            # Step 4: Extract tables with multi-page handling
            if self.table_extraction_enabled:
                self.logger.info("Starting table extraction with multi-page handling...")
                await self._extract_and_merge_tables(page_images_folder)
            
            # Step 5: Store all data in database
            await self._store_page_data(all_results)
            await self._store_table_data()
            
            # Step 6: Update PDF status
            self.pdf_record.processing_status = "completed"
            await self.db_session.commit()
            
            # Step 7: Clean up temporary files and any files in public folder
            self._cleanup_temp_files()
            self._cleanup_public_folder()
            
            # Calculate statistics
            total_time = time.time() - start_time
            total_pages = len(all_results)
            total_images = sum(len(page.get("embedded_images", [])) for page in all_results)
            total_tables = len(self.processed_tables)
            
            self.logger.info(f"Processing completed successfully in {total_time:.2f} seconds")
            self.logger.info(f"Pages: {total_pages}, Images: {total_images}, Tables: {total_tables}")
            
            return {
                "success": True,
                "pdf_id": self.pdf_record.id,
                "processing_time": total_time,
                "pages_processed": total_pages,
                "images_extracted": total_images,
                "tables_extracted": total_tables
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            if self.pdf_record:
                self.pdf_record.processing_status = "failed"
                await self.db_session.commit()
            self._cleanup_temp_files()
            self._cleanup_public_folder()
            return {"success": False, "error": str(e)}
    
    def _process_page_batch(self, page_nums: List[int], page_images_folder: str, embedded_images_folder: str) -> List[Dict]:
        """
        Process a batch of pages from the PDF file.
        """
        results = []
        
        # Open the PDF once for this batch
        doc = fitz.open(self.pdf_path)
        
        for page_num in page_nums:
            start_time = time.time()
            self.logger.info(f"Processing page {page_num + 1}")
            
            # Get the specific page
            page = doc[page_num]
            
            # STEP 1: Detect page orientation
            rotation_needed = self._detect_orientation(page)
            
            # STEP 2: Extract text with fallback methods
            page_text, extraction_method = self._extract_text(page)
            
            # STEP 3: Extract embedded images from the page
            embedded_images = self._extract_embedded_images(doc, page, page_num, embedded_images_folder)
            
            # STEP 4: Render the page as an image
            page_image_path = self._render_page_image(
                pdf_path=self.pdf_path,
                page_num=page_num,
                rotation=rotation_needed,
                output_folder=page_images_folder
            )
            
            # STEP 5: Create page data with all extracted information
            page_data = {
                "page": page_num + 1,
                "page_content": page_text,
                "extraction_method": extraction_method,
                "rotation": rotation_needed,
                "processing_time": time.time() - start_time,
                "page_image_path": page_image_path,
                "embedded_images": embedded_images
            }
            
            results.append(page_data)
            
            # Log completion of this page
            self.logger.info(
                f"Completed page {page_num + 1}: "
                f"Extracted {len(page_text.split())} words using {extraction_method}, "
                f"rotation={rotation_needed}°, "
                f"images={len(embedded_images)}"
            )
        
        # Close the document after processing all pages in the batch
        doc.close()
        
        return results
    
    async def _extract_and_merge_tables(self, images_folder: str):
        """Extract tables with multi-page handling using similarity checking."""
        if not self.api_keys or len(self.api_keys) == 0:
            self.logger.error("No valid Gemini API keys found. Cannot extract tables.")
            return
        
        self.logger.info(f"Extracting tables with {len(self.api_keys)} API keys")
        key_manager = ApiKeyManager(self.api_keys)
        
        # Find all image files sorted by page number
        image_files = []
        for entry in os.listdir(images_folder):
            file_path = os.path.join(images_folder, entry)
            if os.path.isfile(file_path) and any(file_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                # Extract page number
                page_number = 999999
                if entry.startswith("page_"):
                    try:
                        page_str = entry.replace("page_", "").split(".")[0]
                        page_number = int(page_str)
                    except (ValueError, IndexError):
                        pass
                image_files.append((page_number, entry, file_path))
        
        # Sort by page number
        image_files.sort(key=lambda x: x[0])
        
        # Process each page sequentially for proper table merging
        for page_number, filename, file_path in image_files:
            self.logger.info(f"Processing page {page_number} for tables")
            
            # Extract tables from this page
            page_tables = await self._extract_tables_from_page(file_path, page_number, key_manager)
            
            # Check for multi-page table continuation
            if page_tables and self.processed_tables:
                merged_any = await self._check_and_merge_tables(page_tables)
                
                # Add remaining unmerged tables
                for table in page_tables:
                    if not hasattr(table, '_merged'):
                        self.processed_tables.append(table)
            elif page_tables:
                # First page or no previous tables
                self.processed_tables.extend(page_tables)
    
    async def _extract_tables_from_page(self, image_path: str, page_number: int, key_manager) -> List[TableInfo]:
        """Extract tables from a single page using structured LLM output."""
        try:
            image = Image.open(image_path)
        except Exception as e:
            self.logger.error(f"Failed to open image {image_path}: {e}")
            return []
        
        thread_id = threading.get_ident()
        client, current_key = key_manager.get_client(thread_id)
        
        try:
            prompt = """
            Analyze this image for tables and return a JSON response with this exact structure:
            
            {
              "tables": [
                {
                  "table_id": 1,
                  "title": "descriptive_table_name",
                  "markdown_content": "| col1 | col2 |\\n|------|------|\\n| val1 | val2 |",
                  "column_headers": ["col1", "col2"],
                  "row_count": 1,
                  "column_count": 2,
                  "has_header": true
                }
              ]
            }
            
            Guidelines:
            1. If no tables found, return {"tables": []}
            2. Each table gets a descriptive title (SQL-compatible, under 50 chars, lowercase_with_underscores)
            3. Column headers should be lowercase with underscores, no spaces
            4. Include complete markdown table with ALL data visible
            5. Count only data rows (excluding header row)
            6. If table appears to continue from previous page, add "_continued" to title
            7. If table appears incomplete/cut-off, add "_partial" to title
            8. Ensure JSON is valid - escape newlines as \\n
            
            Return ONLY the JSON, no other text.
            """
            
            # Make API call with rate limiting
            current_time = time.time()
            elapsed_time = current_time - key_manager.last_request_time.get(current_key, 0)
            if elapsed_time < key_manager.request_interval:
                sleep_time = key_manager.request_interval - elapsed_time + 0.1
                time.sleep(sleep_time)
            
            key_manager.last_request_time[current_key] = time.time()
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[image, prompt]
            )
            
            if not response or not response.text:
                self.logger.warning(f"No response for page {page_number}")
                return []
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            try:
                result = json.loads(response_text)
                tables_data = result.get("tables", [])
                
                # Convert to TableInfo objects
                tables = []
                for i, table_data in enumerate(tables_data):
                    table_info = TableInfo(
                        table_id=table_data.get("table_id", i + 1),
                        title=table_data.get("title", f"table_{page_number}_{i+1}"),
                        start_page=page_number,
                        end_page=page_number,
                        markdown_content=table_data.get("markdown_content", ""),
                        column_headers=table_data.get("column_headers", []),
                        row_count=table_data.get("row_count", 0),
                        column_count=table_data.get("column_count", 0)
                    )
                    tables.append(table_info)
                
                self.logger.info(f"Extracted {len(tables)} tables from page {page_number}")
                return tables
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response for page {page_number}: {e}")
                self.logger.error(f"Raw response: {response_text[:500]}...")
                return []    
        except Exception as e:
            self.logger.error(f"Error extracting tables from page {page_number}: {e}")
            return []
        finally:
            key_manager.release_client(current_key, thread_id)
    
    async def _check_and_merge_tables(self, new_page_tables: List[TableInfo]) -> bool:
        """Check if any new tables should be merged with previous page tables."""
        if not new_page_tables or not self.processed_tables:
            return False
        
        merged_any = False
        last_table = self.processed_tables[-1]
        
        for new_table in new_page_tables[:]:  # Copy list to avoid modification issues
            if await self._should_merge_tables(last_table, new_table):
                self.logger.info(f"Merging table '{new_table.title}' with '{last_table.title}'")
                
                # Merge the tables
                merged_content = self._merge_table_content(last_table.markdown_content, new_table.markdown_content)
                
                # Update the last table
                last_table.markdown_content = merged_content
                last_table.end_page = new_table.end_page
                last_table.row_count += new_table.row_count
                
                # Update title to remove partial indicators
                if "_partial" in last_table.title:
                    last_table.title = last_table.title.replace("_partial", "")
                
                # Mark as merged
                new_table._merged = True
                merged_any = True
                break  # Only merge with one table per page
        
        return merged_any
    
    async def _should_merge_tables(self, table1: TableInfo, table2: TableInfo) -> bool:
        """Determine if two tables should be merged using LLM similarity check."""
        # Quick checks first
        if table1.column_count != table2.column_count:
            return False
        
        if not table1.column_headers or not table2.column_headers:
            return False
        
        # Check for naming hints
        if "_partial" in table1.title or "_continued" in table2.title:
            # Additional LLM check for confirmation
            pass
        
        # Use LLM for similarity check
        prompt = f"""
        Analyze if these two tables are parts of the same table spanning multiple pages.
        
        Table 1 (Page {table1.start_page}):
        Title: {table1.title}
        Columns: {table1.column_headers}
        Sample: {table1.markdown_content[:300]}...
        
        Table 2 (Page {table2.start_page}):
        Title: {table2.title}
        Columns: {table2.column_headers}
        Sample: {table2.markdown_content[:300]}...
        
        Consider:
        1. Identical column headers
        2. Similar table structure
        3. Logical content continuation
        4. Naming patterns (partial/continued)
        
        Answer with ONLY "YES" or "NO"
        """
        
        try:
            # Use first available API key for quick check
            if self.api_keys:
                client = genai.Client(api_key=self.api_keys[0])
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=[prompt]
                )
                
                if response and response.text:
                    result = response.text.strip().upper()
                    self.logger.info(f"Similarity check result: {result}")
                    return result == "YES"
        except Exception as e:
            self.logger.error(f"Error in similarity check: {e}")
        
        # Fallback to simple header comparison
        headers_match = table1.column_headers == table2.column_headers
        self.logger.info(f"Fallback header comparison: {headers_match}")
        return headers_match
    
    def _merge_table_content(self, content1: str, content2: str) -> str:
        """Merge two markdown tables by combining their rows."""
        try:
            lines1 = content1.strip().split('\n')
            lines2 = content2.strip().split('\n')
            
            # Find header separator in second table and skip header
            skip_lines = 0
            for i, line in enumerate(lines2):
                if '---' in line:
                    skip_lines = i + 1
                    break
            
            # Combine: first table + data rows from second table
            merged_lines = lines1 + lines2[skip_lines:]
            return '\n'.join(merged_lines)
        except Exception as e:
            self.logger.error(f"Error merging table content: {e}")
            return content1  # Return original if merge fails
    
    async def _store_page_data(self, page_results: List[Dict]):
        """Store page text and images in database."""
        for page_data in page_results:
            page_num = page_data["page"]
            
            # Store page text
            page_text = PageText(
                pdf_id=self.pdf_record.id,
                page_number=page_num,
                extracted_text=page_data["page_content"]
            )
            self.db_session.add(page_text)
            
            # Store embedded images
            for img_data in page_data.get("embedded_images", []):
                # Upload image to Cloudinary
                img_path = os.path.join(self.temp_folder, "embedded_images", f"page{page_num}image{img_data['index']}.{img_data['extension']}")
                
                if os.path.exists(img_path):
                    try:
                        with open(img_path, 'rb') as img_file:
                            upload_result = await storage_service.upload_image(
                                image_data=img_file,
                                folder=f"pdf_images/pdf_{self.pdf_record.id}",
                                public_id=f"page_{page_num}_img_{img_data['index']}"
                            )
                        
                        # Create database record
                        image_record = ImageModel(
                            pdf_id=self.pdf_record.id,
                            page_number=page_num,
                            cloudinary_url=upload_result["url"]
                        )
                        self.db_session.add(image_record)
                        
                    except Exception as e:
                        self.logger.error(f"Error uploading image {img_path}: {e}")
        
        await self.db_session.commit()
        self.logger.info("Stored page data in database")
    
    async def _store_table_data(self):
        """Store extracted tables in database."""
        for table_info in self.processed_tables:
            table_record = Table(
                pdf_id=self.pdf_record.id,
                start_page=table_info.start_page,
                end_page=table_info.end_page,
                table_number=table_info.table_id,
                table_title=table_info.title,
                markdown_content=table_info.markdown_content,
                column_count=table_info.column_count,
                row_count=table_info.row_count
            )
            self.db_session.add(table_record)
        
        await self.db_session.commit()
        self.logger.info(f"Stored {len(self.processed_tables)} tables in database")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files and folders."""
        try:
            if os.path.exists(self.temp_folder):
                shutil.rmtree(self.temp_folder)
                self.logger.info(f"Cleaned up temporary folder: {self.temp_folder}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")
    
    def _cleanup_public_folder(self):
        """Clean up any files in public folder related to this processing."""
        try:
            public_folder = "public"
            if os.path.exists(public_folder):
                # Look for any files that might have been created during processing
                for root, dirs, files in os.walk(public_folder):
                    for file in files:
                        if self.file_id in file or "pdf_" in file:
                            file_path = os.path.join(root, file)
                            os.remove(file_path)
                            self.logger.info(f"Removed file from public folder: {file_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up public folder: {e}")

    # Keep all existing helper methods but modify as needed
    
    def _detect_orientation(self, page) -> int:
        """
        Detect text orientation on the page to determine if rotation is needed.
        """
        rotation_needed = 0
        blocks = page.get_text("dict").get("blocks", [])
        
        if blocks:
            # Function to get direction from a line
            def get_direction(line):
                if "dir" in line and isinstance(line["dir"], (list, tuple)) and len(line["dir"]) >= 2:
                    x, y = line["dir"][0], line["dir"][1]
                    if abs(x) > abs(y):  # Horizontal-dominant orientation
                        if x < 0:  # Right-to-left
                            return 180
                        else:
                            return 0
                    else:  # Vertical-dominant orientation
                        if y > 0:  # Bottom-to-top
                            return 90
                        elif y < 0:  # Top-to-bottom but vertical
                            return 270
                return 0  # Default: no rotation
            
            # Get the first text piece's direction
            first_dir = None
            if len(blocks) > 0 and blocks[len(blocks)//2].get("lines") and blocks[len(blocks)//2]["lines"]:
                first_dir = get_direction(blocks[len(blocks)//2]["lines"][0])
            
            # Get the last text piece's direction
            mid_dir = None
            if len(blocks) > 0:
                mid_block = blocks[len(blocks)//2+1]
                if mid_block.get("lines") and mid_block["lines"]:
                    mid_dir = get_direction(mid_block["lines"][-1])
            
            # Only rotate if the directions are different
            if first_dir is not None and mid_dir is not None and first_dir == mid_dir:
                # Use the first direction as the rotation needed
                rotation_needed = first_dir
        
        return rotation_needed
    
    def _extract_text(self, page) -> Tuple[str, str]:
        """
        Extract text from a page using multiple fallback methods.
        """
        # Try different extraction modes in sequence
        extraction_modes = ["text", "blocks", "words", "html"]
        
        for mode in extraction_modes:
            page_text = page.get_text(mode)
            
            # Process the text based on the mode
            if mode == "blocks" and isinstance(page_text, list):
                # Blocks mode returns a list of tuples, concatenate them
                blocks_text_content = ""
                for block in page_text:
                    if isinstance(block, tuple) and len(block) >= 4:
                        blocks_text_content += str(block[4]) + "\n"
                    elif isinstance(block, str):
                        blocks_text_content += block + "\n"
                page_text = blocks_text_content
                
            elif mode == "words" and isinstance(page_text, list):
                # Words mode returns a list of tuples, concatenate them
                words_text_content = ""
                for word in page_text:
                    if isinstance(word, tuple) and len(word) >= 4:
                        words_text_content += str(word[4]) + " "
                    elif isinstance(word, str):
                        words_text_content += word + " "
                page_text = words_text_content
                
            elif mode == "html" and isinstance(page_text, str):
                # Extract text from HTML
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(page_text, 'html.parser')
                    page_text = soup.get_text()
                except ImportError:
                    self.logger.warning("BeautifulSoup not installed, using HTML text as-is")
            
            # If we have meaningful text content, return it
            if page_text and page_text.strip():
                return page_text.strip(), mode
        
        # If all extraction modes fail, try OCR as a last resort
        self.logger.info("All text extraction modes failed. Trying OCR fallback.")
        try:
            import pytesseract
            
            # Render page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Extract text with OCR
            ocr_text = pytesseract.image_to_string(img, lang="eng")
            if ocr_text.strip():
                return ocr_text.strip(), "ocr"
        except ImportError:
            self.logger.warning("OCR fallback failed: pytesseract not installed")
        
        # If everything fails, return empty string
        return "", "none"
    
    def _extract_embedded_images(self, doc, page, page_num: int, images_folder: str) -> List[Dict]:
        """
        Extract embedded images from a page.
        """
        page_images = []
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Create the image file name
                image_filename = f"page{page_num+1}image{img_index}.{image_ext}"
                image_path = os.path.join(images_folder, image_filename)

                # Save the image to disk temporarily
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                page_images.append({
                    "index": img_index,
                    "extension": image_ext,
                    "mime_type": f"image/{image_ext}",
                    "path": image_path,  # Store full path for later processing
                    "filename": image_filename
                })
                
            except Exception as e:
                self.logger.error(f"Error extracting image {img_index} from page {page_num+1}: {e}")

        return page_images
    
    def _render_page_image(self, pdf_path: str, page_num: int, rotation: int, output_folder: str) -> str:
        """
        Render a PDF page as image and save it to disk.
        """
        # Use pdf2image to extract the image of this specific page
        dpi = 150  # Higher DPI for better quality
        images = convert_from_path(
            pdf_path, 
            dpi=dpi, 
            first_page=page_num+1, 
            last_page=page_num+1
        )
        
        image_path = ""
        if images:
            img = images[0]
            
            # Apply rotation if needed
            if rotation != 0:
                img = img.rotate(rotation, expand=True)
            
            # Save the image
            image_filename = f"page_{page_num + 1:03d}.png"
            image_path = os.path.join(output_folder, image_filename)
            img.save(image_path)
        
        return image_path

# Example usage function for FastAPI integration
async def process_pdf_async(pdf_path: str, filename: str, user_id: int, db_session: AsyncSession) -> Dict[str, Any]:
    """
    Async wrapper function for processing PDFs in FastAPI.
    
    Args:
        pdf_path (str): Path to the uploaded PDF file
        filename (str): Original filename
        user_id (int): ID of the user uploading the PDF
        db_session (AsyncSession): Database session
        
    Returns:
        Dict[str, Any]: Processing results
    """
    processor = PDFProcessor(pdf_path, user_id, db_session)
    return await processor.process_pdf(filename)
