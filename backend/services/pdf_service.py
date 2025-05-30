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

# Import our MongoDB models and services
from models.user import User
from models.pdf import PDF
from models.page_text import PageText
from models.table import Table
from models.image import Image as ImageModel
from services.storage_service import storage_service
from utils.pydantic_objectid import PyObjectId

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
    """
    Perfect thread-safe API key manager with rate limiting and intelligent key rotation.
    Absolutely bulletproof implementation for high-throughput PDF processing.
    """
    
    def __init__(self, api_keys: List[str]):
        """Initialize with bulletproof validation and error handling."""
        if not api_keys or len(api_keys) == 0:
            raise ValueError("At least one API key is required")
        
        self.request_interval = 0.2  # 200ms minimum between requests per key
        self.logger = logging.getLogger("ApiKeyManager")
        
        # Validate and initialize clients
        self.clients: Dict[str, genai.Client] = {}
        self.last_request_time: Dict[str, float] = {}
        valid_keys: List[str] = []
        
        for key in api_keys:
            try:
                client = genai.Client(api_key=key)
                # Optional: Uncomment next line to validate keys at startup
                # client.models.list()
                self.clients[key] = client
                self.last_request_time[key] = 0.0
                valid_keys.append(key)
                self.logger.debug("Successfully initialized client for API key")
            except Exception as e:
                self.logger.error(f"Failed to initialize client for API key: {e}")
        
        if not valid_keys:
            raise ValueError("No valid API keys could be initialized")
        
        self.api_keys = valid_keys  # Only store valid keys
        
        # Thread safety with reentrant lock
        self._lock = threading.RLock()
        
        # Simple and efficient thread -> key mapping
        self._thread_assignments: Dict[int, str] = {}  # thread_id -> api_key
        self._key_owners: Dict[str, Optional[int]] = {key: None for key in self.api_keys}
        
        # Round-robin for fairness
        self._next_key_index = 0
        
        self.logger.info(f"ApiKeyManager initialized with {len(self.api_keys)} valid keys")
    
    def get_client(self, thread_id: int) -> Tuple[genai.Client, str]:
        """Get an API client for the current thread with perfect error handling."""
        with self._lock:
            # Check existing assignment
            if thread_id in self._thread_assignments:
                assigned_key = self._thread_assignments[thread_id]
                if self._key_owners.get(assigned_key) == thread_id:
                    return self.clients[assigned_key], assigned_key
                else:
                    # Clean up stale assignment
                    del self._thread_assignments[thread_id]
            
            # Find best available key
            best_key = self._find_best_available_key()
            
            # Clean up any previous assignment for this key
            old_owner = self._key_owners[best_key]
            if old_owner is not None:
                if old_owner in self._thread_assignments:
                    del self._thread_assignments[old_owner]
                self.logger.debug(f"Reassigned key from thread {old_owner} to thread {thread_id}")
            
            # Assign key to current thread
            self._thread_assignments[thread_id] = best_key
            self._key_owners[best_key] = thread_id
            
            self.logger.debug(f"Thread {thread_id} assigned API key")
            return self.clients[best_key], best_key
    
    def _find_best_available_key(self) -> str:
        """Find the optimal key using intelligent selection strategy."""
        current_time = time.time()
        
        # Strategy 1: Prioritize completely unassigned keys
        for key in self.api_keys:
            if self._key_owners[key] is None:
                return key
        
        # Strategy 2: Find the key that's been idle longest
        best_key = min(self.api_keys, key=lambda k: self.last_request_time[k])
        
        # Strategy 3: If all keys were used recently, use fair round-robin
        if current_time - self.last_request_time[best_key] < self.request_interval:
            best_key = self.api_keys[self._next_key_index % len(self.api_keys)]
            self._next_key_index = (self._next_key_index + 1) % len(self.api_keys)
        
        return best_key
    
    def release_client(self, key: str, thread_id: int) -> None:
        """Release a client with ownership verification."""
        with self._lock:
            if (thread_id in self._thread_assignments and 
                self._thread_assignments[thread_id] == key and
                self._key_owners.get(key) == thread_id):
                
                del self._thread_assignments[thread_id]
                self._key_owners[key] = None
                self.logger.debug(f"Thread {thread_id} released API key")
            else:
                self.logger.warning(f"Thread {thread_id} tried to release key it doesn't own")
    
    def update_request_time(self, key: str) -> None:
        """Update the last request time for perfect rate limiting."""
        self.last_request_time[key] = time.time()
    
    def get_wait_time(self, key: str) -> float:
        """Calculate precise wait time before using this key again."""
        elapsed = time.time() - self.last_request_time.get(key, 0)
        wait_time = self.request_interval - elapsed
        return max(0.0, wait_time)  # Never return negative wait time
    
    def should_wait_for_key(self, key: str) -> bool:
        """Check if we should wait before using this key."""
        return self.get_wait_time(key) > 0
    
    def get_stats(self) -> Dict[str, any]:
        """Get comprehensive usage statistics."""
        with self._lock:
            assigned_count = sum(1 for owner in self._key_owners.values() if owner is not None)
            return {
                "total_keys": len(self.api_keys),
                "assigned_keys": assigned_count,
                "available_keys": len(self.api_keys) - assigned_count,
                "active_threads": len(self._thread_assignments),
                "request_interval": self.request_interval
            }
    
    def force_release_all(self) -> None:
        """Emergency cleanup - force release all assignments."""
        with self._lock:
            self._thread_assignments.clear()
            for key in self._key_owners:
                self._key_owners[key] = None
            self.logger.info("Emergency cleanup: all key assignments released")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with guaranteed cleanup."""
        self.force_release_all()

class PDFProcessor:
    """
    Enhanced PDF processor with MongoDB integration that:
    1. Extracts and saves pages as images with proper rotation
    2. Extracts text using multiple fallback methods
    3. Extracts embedded images from the PDF
    4. Handles multi-page tables with LLM-based similarity checking
    5. Stores everything in MongoDB via Cloudinary
    6. Cleans up temporary files
    7. Requires authentication
    """
    
    def __init__(self, pdf_path: str, user_id: str, temp_folder: str = None):
        """
        Initialize the PDF processor.

        Args:
            pdf_path (str): Path to the PDF file
            user_id (str): MongoDB ObjectId of the user uploading the PDF
            temp_folder (str): Temporary folder for processing (will be cleaned up)
        """
        self.pdf_path = pdf_path
        self.user_id = PyObjectId(user_id)
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

        # FIXED: Load Gemini API keys with proper comma handling
        load_dotenv()
        gemini_keys_string = os.getenv("GEMINI_KEYS", "")

        if not gemini_keys_string.strip():
            self.logger.warning("No GEMINI_KEYS found in environment variables. Table extraction will be disabled.")
            self.api_keys = []
            self.table_extraction_enabled = False
        else:
            # Split by comma and clean up each key (remove whitespace, filter empty)
            self.api_keys = [key.strip() for key in gemini_keys_string.split(",") if key.strip()]

            if not self.api_keys:
                self.logger.warning("GEMINI_KEYS contains no valid keys. Table extraction will be disabled.")
                self.table_extraction_enabled = False
            else:
                self.logger.info(f"Loaded {len(self.api_keys)} Gemini API keys from environment")
                self.table_extraction_enabled = True

        # Store for multi-page table tracking
        self.processed_tables: List[TableInfo] = []

        # PDF database record
        self.pdf_record: Optional[PDF] = None


    async def process_pdf(self, filename: str, num_workers: int = 4) -> Dict[str, Any]:
        """
        Process a PDF file and store everything in MongoDB.
        
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
            
            # Verify user exists and is active
            user = await User.get(self.user_id)
            if not user or not user.is_active:
                self.logger.error(f"User {self.user_id} not found or inactive")
                return {"success": False, "error": "User not found or inactive"}
            
            # Step 1: Upload PDF to Cloudinary
            self.logger.info("Uploading PDF to Cloudinary...")
            with open(self.pdf_path, 'rb') as pdf_file:
                # Create a temporary UploadFile-like object for the storage service
                class TempUploadFile:
                    def __init__(self, file_content, filename):
                        self.content = file_content
                        self.filename = filename
                        self._position = 0
                    
                    async def read(self):
                        return self.content
                    
                    async def seek(self, position):
                        self._position = position
                
                temp_file = TempUploadFile(pdf_file.read(), filename)
                upload_result = await storage_service.upload_document(
                    file=temp_file,
                    folder="user_documents",
                    public_id=f"user_{self.user_id}_{self.file_id}"
                )
            
            # Step 2: Create PDF record in MongoDB
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
            
            await self.pdf_record.insert()
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
            cpu_count = min(12, num_workers)
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
            
            # Step 5: Store all data in MongoDB
            await self._store_page_data(all_results)
            await self._store_table_data()
            
            # Step 6: Update PDF status
            self.pdf_record.processing_status = "completed"
            await self.pdf_record.save()
            
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
                "pdf_id": str(self.pdf_record.id),
                "processing_time": total_time,
                "pages_processed": total_pages,
                "images_extracted": total_images,
                "tables_extracted": total_tables,
                "cloudinary_url": upload_result["url"]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            if self.pdf_record:
                self.pdf_record.processing_status = "failed"
                await self.pdf_record.save()
            self._cleanup_temp_files()
            self._cleanup_public_folder()
            return {"success": False, "error": str(e)}
    
    def _process_page_batch(self, page_nums: List[int], page_images_folder: str, embedded_images_folder: str) -> List[Dict]:
        """
        Process a batch of pages from the PDF file with comprehensive error handling.
        """
        results = []

        try:
            # Open the PDF once for this batch
            doc = fitz.open(self.pdf_path)

            for page_num in page_nums:
                try:
                    start_time = time.time()
                    self.logger.info(f"Processing page {page_num + 1}")

                    # Get the specific page
                    page = doc[page_num]

                    # STEP 1: Detect page orientation (with error handling)
                    try:
                        rotation_needed = self._detect_orientation(page)
                    except Exception as e:
                        self.logger.error(f"Error detecting orientation for page {page_num + 1}: {e}")
                        rotation_needed = 0

                    # STEP 2: Extract text with fallback methods
                    try:
                        page_text, extraction_method = self._extract_text(page)
                        if not page_text:
                            self.logger.warning(f"No text extracted from page {page_num + 1}")
                    except Exception as e:
                        self.logger.error(f"Error extracting text from page {page_num + 1}: {e}")
                        page_text, extraction_method = "", "failed"

                    # STEP 3: Extract embedded images from the page
                    try:
                        embedded_images = self._extract_embedded_images(doc, page, page_num, embedded_images_folder)
                    except Exception as e:
                        self.logger.error(f"Error extracting images from page {page_num + 1}: {e}")
                        embedded_images = []

                    # STEP 4: Render the page as an image
                    try:
                        page_image_path = self._render_page_image(
                            pdf_path=self.pdf_path,
                            page_num=page_num,
                            rotation=rotation_needed,
                            output_folder=page_images_folder
                        )
                    except Exception as e:
                        self.logger.error(f"Error rendering page {page_num + 1} as image: {e}")
                        page_image_path = ""

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
                    word_count = len(page_text.split()) if page_text else 0
                    self.logger.info(
                        f"Completed page {page_num + 1}: "
                        f"Extracted {word_count} words using {extraction_method}, "
                        f"rotation={rotation_needed}°, "
                        f"images={len(embedded_images)}"
                    )

                except Exception as e:
                    self.logger.error(f"Error processing page {page_num + 1}: {e}")
                    # Add empty page data to maintain page count
                    results.append({
                        "page": page_num + 1,
                        "page_content": "",
                        "extraction_method": "failed",
                        "rotation": 0,
                        "processing_time": 0,
                        "page_image_path": "",
                        "embedded_images": []
                    })

            # Close the document after processing all pages in the batch
            doc.close()

        except Exception as e:
            self.logger.error(f"Error opening PDF document: {e}")
            # Return empty results for failed pages
            for page_num in page_nums:
                results.append({
                    "page": page_num + 1,
                    "page_content": "",
                    "extraction_method": "failed",
                    "rotation": 0,
                    "processing_time": 0,
                    "page_image_path": "",
                    "embedded_images": []
                })

        return results

    
    async def _extract_and_merge_tables(self, images_folder: str):
        """Extract tables with multi-page handling using parallel processing and similarity checking."""
        if not self.table_extraction_enabled or not self.api_keys:
            self.logger.error("No valid Gemini API keys found. Cannot extract tables.")
            return
        
        self.logger.info(f"Starting PARALLEL table extraction with {len(self.api_keys)} API keys")
        
        # FIXED: Use context manager for proper cleanup
        with ApiKeyManager(self.api_keys) as key_manager:
            # Find all image files sorted by page number
            image_files = []
            try:
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
            except Exception as e:
                self.logger.error(f"Error scanning images folder: {e}")
                return
            
            # Sort by page number
            image_files.sort(key=lambda x: x[0])
            
            if not image_files:
                self.logger.warning("No page images found for table extraction")
                return
            
            self.logger.info(f"Found {len(image_files)} page images for table extraction")
            
            # OPTIMIZED: Process up to 3 pages in parallel (respecting API limits)
            max_parallel = min(len(self.api_keys), 10, len(image_files))
            semaphore = asyncio.Semaphore(max_parallel)
            
            async def extract_with_semaphore(image_data):
                """Extract tables with semaphore control for rate limiting"""
                page_number, filename, file_path = image_data
                async with semaphore:
                    try:
                        self.logger.info(f"Processing page {page_number} for tables")
                        tables = await self._extract_tables_from_page(file_path, page_number, key_manager)
                        return page_number, tables
                    except Exception as e:
                        self.logger.error(f"Error extracting tables from page {page_number}: {e}")
                        return page_number, []
            
            # Extract tables from all pages in parallel
            self.logger.info(f"Processing table extraction with {max_parallel} parallel workers...")
            tasks = [extract_with_semaphore(img_data) for img_data in image_files]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"Error in parallel table extraction: {e}")
                return
            
            # Process results sequentially for proper table merging
            page_results = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Exception in parallel table extraction: {result}")
                    continue
                    
                page_number, page_tables = result
                if page_tables:
                    page_results.append((page_number, page_tables))
                    self.logger.info(f"Page {page_number}: extracted {len(page_tables)} tables")
                else:
                    self.logger.info(f"Page {page_number}: no tables found")
            
            # Sort results by page number for proper sequential merging
            page_results.sort(key=lambda x: x[0])
            
            # Process tables sequentially for multi-page table merging
            for page_number, page_tables in page_results:
                try:
                    # Check for multi-page table continuation
                    if page_tables and self.processed_tables:
                        # Try to merge with previous tables
                        merged_any = await self._check_and_merge_tables(page_tables)
                        
                        # Add remaining unmerged tables
                        for table in page_tables:
                            if not hasattr(table, '_merged'):
                                self.processed_tables.append(table)
                                self.logger.debug(f"Added new table: {table.title}")
                    elif page_tables:
                        # First page or no previous tables
                        self.processed_tables.extend(page_tables)
                        self.logger.info(f"Added {len(page_tables)} tables from page {page_number}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing tables from page {page_number}: {e}")
                    # Still add the tables even if merging fails
                    if page_tables:
                        self.processed_tables.extend(page_tables)
                    continue
        
        # Context manager ensures all keys are released automatically
        total_tables = len(self.processed_tables)
        self.logger.info(f"Parallel table extraction completed: {total_tables} tables processed")
        
        # Log table summary
        if total_tables > 0:
            table_summary = []
            for i, table in enumerate(self.processed_tables):
                pages = f"{table.start_page}" if table.start_page == table.end_page else f"{table.start_page}-{table.end_page}"
                table_summary.append(f"Table {i+1}: '{table.title}' (pages {pages}, {table.row_count} rows)")
            
            self.logger.info("Extracted tables summary:")
            for summary in table_summary:
                self.logger.info(f"  {summary}")


    
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
            # Enhanced prompt for structured output
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
            AND DO NOT GIVE CODE BLOCKS OF JSON OR MARKDOWN. LIKE DO NOT USE "'''json" OR "```json" OR "```markdown" OR "```"
            DO NOT USE ANY MARKDOWN CODE BLOCKS AT ALL. JUST RETURN THE JSON DIRECTLY.
            """

            # Make API call with rate limiting
            current_time = time.time()
            elapsed_time = current_time - key_manager.last_request_time.get(current_key, 0)
            if elapsed_time < key_manager.request_interval:
                sleep_time = key_manager.request_interval - elapsed_time + 0.1
                time.sleep(sleep_time)

            key_manager.last_request_time[current_key] = time.time()

            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-04-17",
                contents=[image, prompt]
            )

            if not response or not response.text:
                self.logger.warning(f"No response for page {page_number}")
                return []

            # FIXED: Parse JSON response with proper variable definition
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```markdown"):
                response_text = response_text[11:].strip()
            elif response_text.startswith("```json"):
                response_text = response_text[7:].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:].strip()
            if response_text.endswith("```"):   
                response_text = response_text[:-3].strip()


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
                client = genai.Client(api_key=self.api_keys[0])  # FIXED: Use first key
                response = client.models.generate_content(
                    model="gemini-2.5-flash-preview-04-17",
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
        """Store page text and images in MongoDB with parallel processing."""
        
        # Collect all page texts for batch insert
        page_texts = []
        all_image_tasks = []
        
        for page_data in page_results:
            page_num = page_data["page"]
            
            # Prepare page text for batch insert
            page_text = PageText(
                pdf_id=self.pdf_record.id,
                page_number=page_num,
                extracted_text=page_data["page_content"]
            )
            page_texts.append(page_text)
            
            # Collect all images for parallel upload
            for img_data in page_data.get("embedded_images", []):
                img_path = os.path.join(
                    self.temp_folder, 
                    "embedded_images", 
                    f"page{page_num}image{img_data['index']}.{img_data['extension']}"
                )
                
                if os.path.exists(img_path):
                    # Create upload task
                    upload_task = self._upload_single_image_async(
                        img_path, page_num, img_data['index'], img_data['extension']
                    )
                    all_image_tasks.append(upload_task)
        
        # PARALLEL EXECUTION
        self.logger.info(f"Starting parallel upload of {len(all_image_tasks)} images...")
        
        # Execute page text storage and image uploads in parallel
        page_text_task = self._store_page_texts_batch(page_texts)
        image_upload_task = self._process_all_image_uploads(all_image_tasks)
        
        # Wait for both to complete
        await asyncio.gather(page_text_task, image_upload_task)
        
        self.logger.info("Completed parallel page data storage")

    async def _store_page_texts_batch(self, page_texts: List[PageText]):
        """Store all page texts in batch"""
        try:
            if page_texts:
                # Use batch insert if available, otherwise insert individually
                try:
                    await PageText.insert_many(page_texts)
                    self.logger.info(f"Batch inserted {len(page_texts)} page texts")
                except AttributeError:
                    # Fallback to individual inserts if batch not available
                    for page_text in page_texts:
                        await page_text.insert()
                    self.logger.info(f"Individually inserted {len(page_texts)} page texts")
        except Exception as e:
            self.logger.error(f"Error storing page texts: {e}")

    async def _upload_single_image_async(self, img_path: str, page_num: int, img_index: int, extension: str) -> Optional[Dict]:
        """Upload a single image asynchronously"""
        try:
            with open(img_path, 'rb') as img_file:
                image_data = img_file.read()
            
            upload_result = await storage_service.upload_image(
                image_data=image_data,
                folder=f"pdf_images/pdf_{self.pdf_record.id}",
                public_id=f"page_{page_num}_img_{img_index}"
            )
            
            return {
                "page_number": page_num,
                "img_index": img_index,
                "cloudinary_url": upload_result["url"],
                "upload_result": upload_result
            }
            
        except Exception as e:
            self.logger.error(f"Error uploading image {img_path}: {e}")
            return None

    async def _process_all_image_uploads(self, upload_tasks: List):
        """Process all image uploads with controlled parallelism"""
        if not upload_tasks:
            return
        
        # Control parallelism to avoid overwhelming Cloudinary
        semaphore = asyncio.Semaphore(10)  # Max 5 concurrent uploads
        
        async def upload_with_semaphore(task):
            async with semaphore:
                return await task
        
        # Execute all uploads with semaphore control
        self.logger.info(f"Uploading {len(upload_tasks)} images with max 5 concurrent uploads...")
        
        results = await asyncio.gather(
            *[upload_with_semaphore(task) for task in upload_tasks],
            return_exceptions=True
        )
        
        # Collect successful uploads for database storage
        image_records = []
        successful_uploads = 0
        failed_uploads = 0
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Image upload exception: {result}")
                failed_uploads += 1
            elif result is not None:
                # Create database record
                image_record = ImageModel(
                    pdf_id=self.pdf_record.id,
                    page_number=result["page_number"],
                    cloudinary_url=result["cloudinary_url"]
                )
                image_records.append(image_record)
                successful_uploads += 1
            else:
                failed_uploads += 1
        
        # Batch insert image records
        if image_records:
            try:
                # Try batch insert first
                try:
                    await ImageModel.insert_many(image_records)
                    self.logger.info(f"Batch inserted {len(image_records)} image records")
                except AttributeError:
                    # Fallback to individual inserts
                    for record in image_records:
                        await record.insert()
                    self.logger.info(f"Individually inserted {len(image_records)} image records")
            except Exception as e:
                self.logger.error(f"Error storing image records: {e}")
        
        self.logger.info(f"Image upload completed: {successful_uploads} successful, {failed_uploads} failed")

    
    async def _store_table_data(self):
        """Store extracted tables in MongoDB."""
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
            await table_record.insert()
        
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
        try:
            rotation_needed = 0
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])

            if not blocks:
                return 0

            # Function to get direction from a line
            def get_direction(line):
                if "dir" in line and isinstance(line["dir"], (list, tuple)) and len(line["dir"]) >= 2:
                    x, y = line["dir"][0], line["dir"][1]  # FIXED: Properly extract x, y values
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

            # Collect directions from text blocks
            directions = []
            for block in blocks[:5]:  # Check first 5 blocks
                if block.get("type") == 0:  # Text block
                    lines = block.get("lines", [])
                    for line in lines[:3]:  # Check first 3 lines per block
                        direction = get_direction(line)
                        if direction != 0:
                            directions.append(direction)

            # Use most common direction if found
            if directions:
                from collections import Counter
                most_common = Counter(directions).most_common(1)
                rotation_needed = most_common[0][0]

            self.logger.debug(f"Detected rotation: {rotation_needed}°")
            return rotation_needed

        except Exception as e:
            self.logger.error(f"Error detecting orientation: {e}")
            return 0


    
    def _extract_text(self, page) -> Tuple[str, str]:
        """
        Extract text from a page using multiple fallback methods with better error handling.
        """
        # Try different extraction modes in sequence
        extraction_modes = ["text", "dict", "blocks", "words"]

        for mode in extraction_modes:
            try:
                self.logger.debug(f"Trying text extraction mode: {mode}")

                if mode == "text":
                    page_text = page.get_text("text")
                    if page_text and page_text.strip():
                        self.logger.debug(f"Successfully extracted {len(page_text)} characters using text mode")
                        return page_text.strip(), mode

                elif mode == "dict":
                    text_dict = page.get_text("dict")
                    blocks = text_dict.get("blocks", [])
                    text_content = ""

                    for block in blocks:
                        if block.get("type") == 0:  # Text block
                            lines = block.get("lines", [])
                            for line in lines:
                                spans = line.get("spans", [])
                                for span in spans:
                                    span_text = span.get("text", "")
                                    if span_text.strip():
                                        text_content += span_text + " "
                            text_content += "\n"

                    if text_content.strip():
                        self.logger.debug(f"Successfully extracted {len(text_content)} characters using dict mode")
                        return text_content.strip(), mode

                elif mode == "blocks":
                    page_text = page.get_text("blocks")
                    if isinstance(page_text, list):
                        blocks_text_content = ""
                        for block in page_text:
                            if isinstance(block, tuple) and len(block) >= 5:
                                block_text = str(block[4])  # Text is at index 4
                                if block_text.strip():
                                    blocks_text_content += block_text + "\n"

                        if blocks_text_content.strip():
                            self.logger.debug(f"Successfully extracted {len(blocks_text_content)} characters using blocks mode")
                            return blocks_text_content.strip(), mode

                elif mode == "words":
                    page_text = page.get_text("words")
                    if isinstance(page_text, list):
                        words_text_content = ""
                        for word in page_text:
                            if isinstance(word, tuple) and len(word) >= 5:
                                word_text = str(word[4])  # Text is at index 4
                                if word_text.strip():
                                    words_text_content += word_text + " "

                        if words_text_content.strip():
                            self.logger.debug(f"Successfully extracted {len(words_text_content)} characters using words mode")
                            return words_text_content.strip(), mode

            except Exception as e:
                self.logger.error(f"Error in {mode} extraction mode: {e}")
                continue
                
        # If all extraction modes fail, try OCR as a last resort
        self.logger.warning("All text extraction modes failed. Trying OCR fallback.")
        try:
            import pytesseract

            # Render page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Extract text with OCR
            ocr_text = pytesseract.image_to_string(img, lang="eng")
            if ocr_text.strip():
                self.logger.info(f"OCR extracted {len(ocr_text)} characters")
                return ocr_text.strip(), "ocr"
        except ImportError:
            self.logger.warning("OCR fallback failed: pytesseract not installed")
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")

        # If everything fails, return empty string
        self.logger.warning("All text extraction methods failed")
        return "", "none"


    
    def _extract_embedded_images(self, doc, page, page_num: int, images_folder: str) -> List[Dict]:
        """
        Extract embedded images from a page with better error handling.
        """
        page_images = []

        try:
            image_list = page.get_images(full=True)
            self.logger.debug(f"Found {len(image_list)} potential images on page {page_num+1}")

            if not image_list:
                return page_images

        except Exception as e:
            self.logger.error(f"Error getting image list from page {page_num+1}: {e}")
            return page_images

        for img_index, img in enumerate(image_list):
            try:
                # FIXED: Properly handle the image tuple structure
                if isinstance(img, (tuple, list)) and len(img) > 0:
                    xref = img[0]  # First element is the xref
                else:
                    self.logger.warning(f"Unexpected image structure on page {page_num+1}: {type(img)}")
                    continue
                    
                # Validate xref is an integer
                if not isinstance(xref, int) or xref <= 0:
                    self.logger.warning(f"Invalid xref on page {page_num+1}: {xref}")
                    continue
                    
                # Extract the image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Validate extracted data
                if not image_bytes or not image_ext:
                    self.logger.warning(f"Empty image data for image {img_index} on page {page_num+1}")
                    continue

                # Skip very small images (likely decorative)
                if len(image_bytes) < 1024:  # Less than 1KB
                    self.logger.debug(f"Skipping small image {img_index} on page {page_num+1} ({len(image_bytes)} bytes)")
                    continue

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
                    "path": image_path,
                    "filename": image_filename,
                    "size_bytes": len(image_bytes)
                })

                self.logger.debug(f"Successfully extracted image {img_index} from page {page_num+1} ({len(image_bytes)} bytes)")

            except Exception as e:
                self.logger.error(f"Error extracting image {img_index} from page {page_num+1}: {e}")
                continue

        self.logger.info(f"Successfully extracted {len(page_images)} images from page {page_num+1}")
        return page_images


    
    def _render_page_image(self, pdf_path: str, page_num: int, rotation: int, output_folder: str) -> str:
        """
        Render a PDF page as image and save it to disk.
        """
        try:
            # Use pdf2image to extract the image of this specific page
            dpi = 150  # Higher DPI for better quality
            images = convert_from_path(
                pdf_path, 
                dpi=dpi, 
                first_page=page_num+1, 
                last_page=page_num+1
            )

            image_path = ""
            if images and len(images) > 0:
                img = images[0]  # FIXED: Get first image from list, not the list itself

                # Apply rotation if needed
                if rotation != 0:
                    img = img.rotate(rotation, expand=True)

                # Save the image
                image_filename = f"page_{page_num + 1:03d}.png"
                image_path = os.path.join(output_folder, image_filename)
                img.save(image_path)

                self.logger.debug(f"Successfully rendered page {page_num+1} as image")
            else:
                self.logger.warning(f"No images generated for page {page_num+1}")

            return image_path

        except Exception as e:
            self.logger.error(f"Error rendering page {page_num+1} as image: {e}")
            return ""


# Async wrapper function for FastAPI integration with authentication
async def process_pdf_async(pdf_path: str, filename: str, user_id: str) -> Dict[str, Any]:
    """
    Async wrapper function for processing PDFs in FastAPI with authentication.
    
    Args:
        pdf_path (str): Path to the uploaded PDF file
        filename (str): Original filename
        user_id (str): MongoDB ObjectId of the authenticated user
        
    Returns:
        Dict[str, Any]: Processing results
    """
    processor = PDFProcessor(pdf_path, user_id)
    return await processor.process_pdf(filename)
