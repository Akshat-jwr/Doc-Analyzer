import sys
import os
import fitz  # PyMuPDF
import datetime
import time
from pdf2image import convert_from_path
import concurrent.futures
import logging
from typing import List, Dict, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil
import asyncio
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from models.document_chunk import DocumentChunk


# Import our MongoDB models and services
from models.user import User
from models.pdf import PDF, ProcessingStatus
from models.page_text import PageText
from models.image import Image as ImageModel
from services.storage_service import storage_service
from utils.pydantic_objectid import PyObjectId

class StreamlinedPDFProcessor:
    """
    ENHANCED processor - PDF, WORD, SPREADSHEETS support
    Spreadsheets: Upload → Convert to MD → Store in DB (all in one process)
    """
    
    def __init__(self, pdf_path: str, user_id: str, temp_folder: str = None):
        """Initialize the streamlined PDF processor"""
        self.pdf_path = pdf_path
        self.user_id = PyObjectId(user_id)
        self.file_id = os.path.basename(pdf_path).replace(' ', '_').split('.')[0]

        # Set up temporary folder
        self.temp_folder = temp_folder or tempfile.mkdtemp(prefix=f"pdf_processing_{self.file_id}_")
        os.makedirs(self.temp_folder, exist_ok=True)

        # Set up logger
        self.logger = self._setup_logger()
        self.pdf_record: Optional[PDF] = None


        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _setup_logger(self) -> logging.Logger:
        """Set up optimized logger configuration"""
        logger = logging.getLogger("StreamlinedPDFProcessor")
        
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger

    def _detect_file_type(self, file_path: str) -> str:
        """🔥 ENHANCED: Detect file type including spreadsheets"""
        try:
            # Try python-magic first
            try:
                import magic
                if hasattr(magic, 'from_file'):
                    return magic.from_file(file_path, mime=True)
            except ImportError:
                pass
            
            # Fallback to header detection
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
                if header.startswith(b'%PDF'):
                    return 'application/pdf'
                elif header.startswith(b'\x89PNG'):
                    return 'image/png'
                elif header.startswith(b'\xff\xd8\xff'):
                    return 'image/jpeg'
                elif header.startswith(b'PK\x03\x04'):
                    # ZIP-based format
                    with open(file_path, 'rb') as zf:
                        content = zf.read(1024)
                        if b'word/' in content:
                            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        elif b'xl/' in content:
                            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # 🔥 XLSX
                        else:
                            return 'application/zip'
                elif header.startswith(b'\xd0\xcf\x11\xe0'):
                    # Could be old Office format
                    return 'application/vnd.ms-excel'  # 🔥 XLS
                else:
                    # Check for CSV (simple text-based detection)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            first_line = f.readline()
                            if ',' in first_line and first_line.count(',') >= 2:
                                return 'text/csv'  # 🔥 CSV
                    except:
                        pass
                    return 'unknown'
                    
        except Exception as e:
            self.logger.warning(f"⚠️ File type detection error: {e}")
            return 'unknown'

    async def _process_spreadsheet_file(self, file_path: str, filename: str) -> Dict[str, Any]:
        """🔥 NEW: Complete spreadsheet processing pipeline"""
        try:
            start_time = time.time()
            
            # Detect specific spreadsheet type
            file_type = self._detect_file_type(file_path)
            self.logger.info(f"📊 Processing spreadsheet: {file_type}")
            
            # Read the spreadsheet file
            if file_type == 'text/csv':
                # CSV file
                df = pd.read_csv(file_path, encoding='utf-8')
                sheets_data = {"CSV_Data": df}
                self.logger.info(f"📊 Read CSV file with {len(df)} rows, {len(df.columns)} columns")
                
            else:
                # Excel file (XLSX/XLS)
                excel_file = pd.ExcelFile(file_path)
                sheets_data = {}
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    sheets_data[sheet_name] = df
                    self.logger.info(f"📊 Read sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns")
            
            # Upload original file to Cloudinary
            self.logger.info("📊 Uploading spreadsheet to Cloudinary...")
            upload_result = await self._upload_spreadsheet_to_cloudinary(file_path, filename)
            
            # Convert to Markdown
            self.logger.info("📊 Converting spreadsheet to Markdown...")
            markdown_content = self._convert_spreadsheet_to_markdown(sheets_data)
            
            # Create PDF record for spreadsheet
            total_pages = len(sheets_data)  # Each sheet = 1 "page"
            self.pdf_record = PDF(
                user_id=self.user_id,
                filename=filename,
                cloudinary_url=upload_result["url"],
                page_count=total_pages,
                processing_status=ProcessingStatus.COMPLETED  # Mark as complete immediately
            )
            await self.pdf_record.insert()
            self.logger.info(f"Created spreadsheet record with ID: {self.pdf_record.id}")
            
            # Store markdown content in database
            await self._store_spreadsheet_markdown(sheets_data, markdown_content)
            
            # Update completion timestamps
            self.pdf_record.text_images_completed_at = datetime.datetime.utcnow()
            self.pdf_record.fully_completed_at = datetime.datetime.utcnow()
            await self.pdf_record.save()
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"✅ Spreadsheet processing completed in {processing_time:.2f}s")
            
            return {
                "success": True,
                "phase": "completed",
                "pdf_id": str(self.pdf_record.id),
                "processing_time": processing_time,
                "pages_processed": total_pages,
                "images_extracted": 0,
                "file_type": "spreadsheet",
                "general_queries_ready": True,
                "analytical_queries_ready": True,
                "cloudinary_url": upload_result["url"],
                "status": f"Spreadsheet processing complete - {total_pages} sheets converted to Markdown",
                "background_processing": False,
                "image_extraction": False,
                "reason": "Spreadsheet files are processed completely in one step"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Spreadsheet processing failed: {e}")
            if self.pdf_record:
                self.pdf_record.processing_status = ProcessingStatus.FAILED
                await self.pdf_record.save()
            return {"success": False, "error": str(e)}

    async def _upload_spreadsheet_to_cloudinary(self, file_path: str, filename: str) -> Dict[str, Any]:
        """🔥 NEW: Upload spreadsheet to Cloudinary"""
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
            
            class SpreadsheetUploadFile:
                def __init__(self, content, filename):
                    self.content = content
                    self.filename = filename
                async def read(self):
                    return self.content
                async def seek(self, position):
                    pass
            
            temp_file = SpreadsheetUploadFile(content, filename)
            return await storage_service.upload_document(
                file=temp_file,
                folder="user_documents",
                public_id=f"user_{self.user_id}_{self.file_id}",
                max_retries=2
            )
            
        except Exception as e:
            raise Exception(f"Failed to upload spreadsheet: {e}")

    def _convert_spreadsheet_to_markdown(self, sheets_data: Dict[str, pd.DataFrame]) -> str:
        """🔥 NEW: Convert spreadsheet data to Markdown format"""
        try:
            markdown_content = ""
            
            for sheet_name, df in sheets_data.items():
                # Clean the dataframe
                df = self._clean_dataframe_for_markdown(df)
                
                # Add sheet header
                markdown_content += f"# {sheet_name}\n\n"
                
                # Convert to markdown with proper handling
                try:
                    # Handle multiline cells by replacing newlines with <br>
                    df_processed = df.copy()
                    for col in df_processed.columns:
                        if df_processed[col].dtype == 'object':
                            df_processed[col] = df_processed[col].astype(str).str.replace('\n', '<br>', regex=False)
                    
                    # Generate markdown table
                    table_markdown = df_processed.to_markdown(index=False, tablefmt='pipe')
                    markdown_content += table_markdown + "\n\n"
                    
                except Exception as e:
                    # Fallback to simple table format
                    self.logger.warning(f"Markdown conversion failed for {sheet_name}, using fallback: {e}")
                    markdown_content += self._create_fallback_markdown_table(df)
                
                # Add summary info
                markdown_content += f"*{sheet_name} contains {len(df)} rows and {len(df.columns)} columns*\n\n"
                markdown_content += "---\n\n"
            
            return markdown_content
            
        except Exception as e:
            self.logger.error(f"❌ Error converting to markdown: {e}")
            return f"# Spreadsheet Data\n\nError converting spreadsheet: {str(e)}"

    def _clean_dataframe_for_markdown(self, df: pd.DataFrame) -> pd.DataFrame:
        """🔥 NEW: Clean dataframe for better Markdown conversion"""
        try:
            # Handle NaN values
            df = df.fillna('')
            
            # Convert all columns to string to handle mixed types
            for col in df.columns:
                df[col] = df[col].astype(str)
            
            # Clean column names (remove special characters that might break markdown)
            df.columns = [str(col).replace('|', '-').replace('\n', ' ').strip() for col in df.columns]
            
            # Limit very long content to prevent massive tables
            for col in df.columns:
                df[col] = df[col].apply(lambda x: str(x)[:500] + '...' if len(str(x)) > 500 else str(x))
            
            # Limit rows if too many (keep first 1000 rows + summary)
            if len(df) > 1000:
                df = df.head(1000)
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error cleaning dataframe: {e}")
            return df

    def _create_fallback_markdown_table(self, df: pd.DataFrame) -> str:
        """🔥 NEW: Create simple markdown table as fallback"""
        try:
            # Create header
            headers = list(df.columns)
            header_row = "| " + " | ".join(headers) + " |\n"
            separator_row = "|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|\n"
            
            # Create data rows
            data_rows = ""
            for _, row in df.head(100).iterrows():  # Limit to 100 rows
                row_data = "| " + " | ".join([str(cell) for cell in row]) + " |\n"
                data_rows += row_data
            
            return header_row + separator_row + data_rows + "\n"
            
        except Exception as e:
            return f"Error creating fallback table: {str(e)}\n\n"

    async def _store_spreadsheet_markdown(self, sheets_data: Dict[str, pd.DataFrame], markdown_content: str):
        """🔥 FIXED: Store spreadsheet content as Table objects (not PageText)"""
        try:
            # Import the Table model
            from models.table import Table
            
            table_records = []
            
            # Create table records for each sheet
            table_number = 1
            for sheet_name, df in sheets_data.items():
                # Generate markdown for this specific sheet
                sheet_markdown = f"# {sheet_name}\n\n"
                try:
                    df_processed = df.copy()
                    for col in df_processed.columns:
                        if df_processed[col].dtype == 'object':
                            df_processed[col] = df_processed[col].astype(str).str.replace('\n', '<br>', regex=False)
                    
                    sheet_markdown += df_processed.to_markdown(index=False, tablefmt='pipe')
                except:
                    sheet_markdown += self._create_fallback_markdown_table(df)
                
                # Create Table record for this sheet
                table_record = Table(
                    pdf_id=self.pdf_record.id,
                    start_page=table_number,  # Each sheet is a "page"
                    end_page=table_number,
                    table_number=table_number,
                    table_title=sheet_name.lower().replace(' ', '_'),
                    markdown_content=sheet_markdown,
                    column_count=len(df.columns),
                    row_count=len(df)
                )
                table_records.append(table_record)
                table_number += 1
            
            # Also store overall markdown as a summary PageText (page 1 only)
            from models.page_text import PageText
            overall_page_text = PageText(
                pdf_id=self.pdf_record.id,
                page_number=1,
                extracted_text=markdown_content  # Complete markdown with all sheets
            )
            
            # Insert table records and summary text
            try:
                # Insert tables
                await Table.insert_many(table_records)
                self.logger.info(f"✅ Stored {len(table_records)} spreadsheet sheets as Table objects")
                
                # Insert summary text
                await overall_page_text.insert()
                self.logger.info(f"✅ Stored overall markdown as PageText")
                
            except AttributeError:
                # Fallback to individual inserts
                for table_record in table_records:
                    await table_record.insert()
                await overall_page_text.insert()
                self.logger.info(f"✅ Individually stored {len(table_records)} tables and 1 page text")
            
            # Update PDF record with table counts
            self.pdf_record.total_tables_found = len(table_records)
            self.pdf_record.tables_processed = len(table_records)
            await self.pdf_record.save()
                
        except Exception as e:
            self.logger.error(f"❌ Error storing spreadsheet as tables: {e}")



    def _diagnose_pdf_integrity(self) -> Dict[str, Any]:
        """Diagnose PDF integrity and page accessibility"""
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            
            problematic_pages = []
            accessible_pages = []
            
            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    # Try to extract some text to test accessibility
                    test_text = page.get_text("text")
                    accessible_pages.append(page_num + 1)
                except Exception as e:
                    problematic_pages.append({"page": page_num + 1, "error": str(e)})
            
            doc.close()
            
            diagnosis = {
                "total_pages": total_pages,
                "accessible_pages": len(accessible_pages),
                "problematic_pages": len(problematic_pages),
                "problems": problematic_pages[:5]  # Show first 5 problems
            }
            
            self.logger.info(f"📋 PDF Diagnosis: {diagnosis}")
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"❌ PDF diagnosis failed: {e}")
            return {"error": str(e)}

    async def process_pdf_phase_1(self, filename: str, num_workers: int = 4) -> Dict[str, Any]:
        """🔥 ENHANCED: Process PDF/Word/Spreadsheet files"""
        start_time = time.time()
        
        try:
            # Quick validations
            if not os.path.exists(self.pdf_path):
                return {"success": False, "error": "File not found"}

            user = await User.get(self.user_id)
            if not user or not user.is_active:
                return {"success": False, "error": "User not found or inactive"}

            # 🔥 NEW: Detect file type first
            file_type = self._detect_file_type(self.pdf_path)
            self.logger.info(f"📄 Detected file type: {file_type}")

            # 🔥 NEW: Handle spreadsheet files
            if file_type in [
                'text/csv',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]:
                self.logger.info(f"📊 Processing as spreadsheet file...")
                return await self._process_spreadsheet_file(self.pdf_path, filename)

            # Continue with existing PDF/Word processing logic
            # Diagnose PDF integrity first
            diagnosis = self._diagnose_pdf_integrity()
            if diagnosis.get("problematic_pages", 0) > 0:
                self.logger.warning(f"⚠️ PDF has {diagnosis['problematic_pages']} problematic pages")

            # Upload PDF to Cloudinary
            self.logger.info("Phase 1: Uploading PDF to Cloudinary...")
            upload_result = await self._upload_pdf_optimized(filename)

            # Get page count and check limits
            num_pages = self._get_page_count()

            # 🔥 Check if PDF exceeds 100 pages
            skip_background_processing = num_pages > 100
            skip_image_extraction = num_pages > 100
            
            if skip_background_processing:
                self.logger.warning(f"⚠️ PDF has {num_pages} pages (> 100) - SKIPPING background table extraction")
            
            if skip_image_extraction:
                self.logger.warning(f"⚠️ PDF has {num_pages} pages (> 100) - SKIPPING image extraction")

            # Create PDF record
            self.pdf_record = PDF(
                user_id=self.user_id,
                filename=filename,
                cloudinary_url=upload_result["url"],
                page_count=num_pages,
                processing_status=ProcessingStatus.PROCESSING
            )
            await self.pdf_record.insert()
            self.logger.info(f"Created PDF record with ID: {self.pdf_record.id}")

            # Create temp folders
            page_images_folder, embedded_images_folder = self._create_temp_folders()

            # CORRECTED: Adaptive worker count and processing
            adaptive_workers = self._calculate_optimal_workers(num_pages, num_workers)

            self.logger.info(f"Phase 1: Processing {num_pages} pages with {adaptive_workers} workers (CORRECTED)")
            all_results = await self._process_pages_corrected(
                num_pages, page_images_folder, embedded_images_folder, adaptive_workers, skip_image_extraction
            )

            # Verify we got all pages
            self.logger.info(f"🔍 VERIFICATION: Processed {len(all_results)} pages out of {num_pages} expected")
            if len(all_results) < num_pages:
                self.logger.warning(f"⚠️ Missing {num_pages - len(all_results)} pages!")

            # Store text and images only
            await self._store_text_and_images_only(all_results, skip_image_extraction)

            # Update status based on page count
            if skip_background_processing:
                # For large PDFs, mark as fully complete (no background processing)
                self.pdf_record.processing_status = ProcessingStatus.COMPLETED
                self.pdf_record.text_images_completed_at = datetime.datetime.utcnow()
                self.pdf_record.fully_completed_at = datetime.datetime.utcnow()
                self.logger.info(f"✅ LARGE PDF ({num_pages} pages) - Marked as COMPLETED (no background processing)")
            else:
                # For smaller PDFs, mark as Phase 1 complete (background will continue)
                self.pdf_record.processing_status = ProcessingStatus.TEXT_IMAGES_COMPLETE
                self.pdf_record.text_images_completed_at = datetime.datetime.utcnow()
                self.logger.info(f"✅ SMALL PDF ({num_pages} pages) - Phase 1 complete, background processing will start")

            await self.pdf_record.save()

            # Cleanup temp files
            self._cleanup_files()

            # Calculate results
            total_time = time.time() - start_time
            total_images = 0 if skip_image_extraction else sum(len(page.get("embedded_images", [])) for page in all_results)

            self.logger.info(f"Phase 1 COMPLETED in {total_time:.2f} seconds")
            self.logger.info(f"Pages: {len(all_results)}, Images: {total_images}")
            if skip_image_extraction:
                self.logger.info("🚫 Image extraction was SKIPPED for large PDF")
            self.logger.info("✅ READY FOR GENERAL QUERIES!")

            # Return different status based on page count
            if skip_background_processing:
                return {
                    "success": True,
                    "phase": "completed",
                    "pdf_id": str(self.pdf_record.id),
                    "processing_time": total_time,
                    "pages_processed": len(all_results),
                    "images_extracted": total_images,
                    "general_queries_ready": True,
                    "analytical_queries_ready": True,  # No tables to extract
                    "cloudinary_url": upload_result["url"],
                    "status": f"Processing Complete - Large PDF ({num_pages} pages) - Background table extraction and image extraction skipped",
                    "background_processing": False,
                    "image_extraction": not skip_image_extraction,
                    "reason": f"PDF has {num_pages} pages (exceeds 100-page limit for table and image extraction)"
                }
            else:
                return {
                    "success": True,
                    "phase": "text_images_complete",
                    "pdf_id": str(self.pdf_record.id),
                    "processing_time": total_time,
                    "pages_processed": len(all_results),
                    "images_extracted": total_images,
                    "general_queries_ready": True,
                    "analytical_queries_ready": False,
                    "cloudinary_url": upload_result["url"],
                    "status": "Phase 1 Complete - Background table extraction will continue",
                    "background_processing": True,
                    "image_extraction": not skip_image_extraction,
                    "reason": f"PDF has {num_pages} pages (within 100-page limit for table and image extraction)"
                }

        except Exception as e:
            self.logger.error(f"Phase 1 processing failed: {str(e)}")
            if self.pdf_record:
                self.pdf_record.processing_status = ProcessingStatus.FAILED
                await self.pdf_record.save()
            self._cleanup_files()
            return {"success": False, "error": str(e)}

    def _calculate_optimal_workers(self, num_pages: int, requested_workers: int) -> int:
        """Calculate optimal number of workers based on PDF size"""
        if num_pages <= 10:
            return min(4, requested_workers)  # Small PDFs: up to 4 workers
        elif num_pages <= 30:
            return min(3, requested_workers)  # Medium PDFs: up to 3 workers  
        elif num_pages <= 100:
            return min(2, requested_workers)  # Large PDFs: up to 2 workers
        else:
            return 1  # Very large PDFs: sequential processing

    async def _process_pages_corrected(self, num_pages: int, page_images_folder: str, 
                                     embedded_images_folder: str, num_workers: int, skip_image_extraction: bool = False) -> List[Dict]:
        """CORRECTED: Process pages with memory management and timeout protection"""
        
        # DEBUGGING: Log the processing plan
        self.logger.info(f"🔍 DEBUGGING: Total pages to process: {num_pages}")
        self.logger.info(f"🔍 DEBUGGING: Using {num_workers} workers")
        if skip_image_extraction:
            self.logger.info(f"🔍 DEBUGGING: Image extraction will be SKIPPED")
        
        # Create smaller batches to prevent memory issues
        pages_per_batch = max(1, min(5, num_pages // num_workers))  # Max 5 pages per batch
        page_nums = list(range(num_pages))
        page_batches = [page_nums[i:i + pages_per_batch] for i in range(0, len(page_nums), pages_per_batch)]
        
        self.logger.info(f"🔍 DEBUGGING: Created {len(page_batches)} batches with {pages_per_batch} pages each")
        for i, batch in enumerate(page_batches):
            self.logger.info(f"🔍 DEBUGGING: Batch {i+1}: pages {[p+1 for p in batch]}")
        
        all_results = []
        
        # Process with controlled threading and timeouts
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_workers,
            thread_name_prefix="corrected_processor"
        ) as executor:
            
            futures = {
                executor.submit(
                    self._process_batch_corrected, 
                    batch, page_images_folder, embedded_images_folder, skip_image_extraction
                ): batch for batch in page_batches
            }
            
            completed_batches = 0
            failed_batches = 0
            
            # Process with timeout for each batch
            for future in concurrent.futures.as_completed(futures, timeout=600):  # 10 minute total timeout
                try:
                    # 3 minute timeout per batch
                    batch_results = future.result(timeout=180)
                    all_results.extend(batch_results)
                    completed_batches += 1
                    batch = futures[future]
                    self.logger.info(f"✅ DEBUGGING: Completed batch {completed_batches}/{len(page_batches)}: pages {[p+1 for p in batch]} - got {len(batch_results)} results")
                    
                except concurrent.futures.TimeoutError:
                    failed_batches += 1
                    batch = futures[future]
                    self.logger.error(f"⏰ DEBUGGING: Batch timeout: pages {[p+1 for p in batch]}")
                    # Add empty results for timeout pages
                    for page_num in batch:
                        all_results.append(self._create_empty_page_data(page_num + 1))
                        
                except Exception as e:
                    failed_batches += 1
                    batch = futures[future]
                    self.logger.error(f"❌ DEBUGGING: Batch error: pages {[p+1 for p in batch]} - {str(e)}")
                    # Add empty results for failed pages
                    for page_num in batch:
                        all_results.append(self._create_empty_page_data(page_num + 1))
        
        self.logger.info(f"🔍 DEBUGGING: Processing summary:")
        self.logger.info(f"  - Completed batches: {completed_batches}")
        self.logger.info(f"  - Failed batches: {failed_batches}")
        self.logger.info(f"  - Total results: {len(all_results)}")
        self.logger.info(f"  - Expected results: {num_pages}")
        
        return sorted(all_results, key=lambda x: x["page"])

    def _process_batch_corrected(self, page_nums: List[int], page_images_folder: str, 
                               embedded_images_folder: str, skip_image_extraction: bool = False) -> List[Dict]:
        """CORRECTED: Process batch with individual document instances for memory management"""
        results = []
        
        # Process each page with its own document instance to prevent memory buildup
        for page_num in page_nums:
            doc = None
            try:
                start_time = time.time()
                self.logger.info(f"Processing page {page_num + 1} (CORRECTED)")
                
                # Open document for this specific page only
                doc = fitz.open(self.pdf_path)
                page = doc[page_num]
                
                # Extract text and images with error handling
                try:
                    rotation_needed = self._detect_orientation_optimized(page)
                except Exception as e:
                    self.logger.warning(f"Orientation detection failed for page {page_num + 1}: {e}")
                    rotation_needed = 0
                
                try:
                    page_text, extraction_method = self._extract_text_optimized(page)
                except Exception as e:
                    self.logger.warning(f"Text extraction failed for page {page_num + 1}: {e}")
                    page_text, extraction_method = "", "failed"
                
                # Conditional image extraction
                if skip_image_extraction:
                    embedded_images = []
                    if page_num == 0:  # Log only once for first page
                        self.logger.info(f"🚫 Skipping image extraction for large PDF")
                else:
                    try:
                        embedded_images = self._extract_embedded_images_optimized(doc, page, page_num, embedded_images_folder)
                    except Exception as e:
                        self.logger.warning(f"Image extraction failed for page {page_num + 1}: {e}")
                        embedded_images = []
                
                try:
                    page_image_path = self._render_page_image_optimized(page_num, rotation_needed, page_images_folder)
                except Exception as e:
                    self.logger.warning(f"Page rendering failed for page {page_num + 1}: {e}")
                    page_image_path = ""
                
                page_data = {
                    "page": page_num + 1,
                    "page_content": page_text,
                    "extraction_method": extraction_method,
                    "rotation": rotation_needed,
                    "processing_time": time.time() - start_time,
                    "page_image_path": page_image_path,
                    "embedded_images": embedded_images  # Will be empty for large PDFs
                }
                
                results.append(page_data)
                
                word_count = len(page_text.split()) if page_text else 0
                image_info = f", {len(embedded_images)} images" if not skip_image_extraction else " (images skipped)"
                self.logger.info(f"✅ Page {page_num + 1}: {word_count} words{image_info}")
                
            except Exception as e:
                self.logger.error(f"❌ CORRECTED: Error processing page {page_num + 1}: {e}")
                results.append(self._create_empty_page_data(page_num + 1))
            finally:
                # CRITICAL: Always close document to free memory
                if doc:
                    doc.close()
                    doc = None
                    
                # Force garbage collection for large PDFs
                if page_num % 10 == 0:  # Every 10 pages
                    import gc
                    gc.collect()
        
        return results

    async def _upload_pdf_optimized(self, filename: str) -> Dict[str, Any]:
        """Optimized PDF upload with compression"""
        with open(self.pdf_path, 'rb') as pdf_file:
            content = pdf_file.read()
        
        class OptimizedUploadFile:
            def __init__(self, content, filename):
                self.content = content
                self.filename = filename
            async def read(self):
                return self.content
            async def seek(self, position):
                pass
        
        temp_file = OptimizedUploadFile(content, filename)
        return await storage_service.upload_document(
            file=temp_file,
            folder="user_documents",
            public_id=f"user_{self.user_id}_{self.file_id}",
            max_retries=2
        )

    def _get_page_count(self) -> int:
        """Get page count efficiently with resource management"""
        doc = fitz.open(self.pdf_path)
        try:
            return len(doc)
        finally:
            doc.close()

    def _create_temp_folders(self) -> Tuple[str, str]:
        """Create temporary folders with optimized paths"""
        page_images_folder = os.path.join(self.temp_folder, "page_images")
        embedded_images_folder = os.path.join(self.temp_folder, "embedded_images")
        os.makedirs(page_images_folder, exist_ok=True)
        os.makedirs(embedded_images_folder, exist_ok=True)
        return page_images_folder, embedded_images_folder

    def _create_empty_page_data(self, page_num: int) -> Dict:
        """Create empty page data for failed pages"""
        return {
            "page": page_num,
            "page_content": "",
            "extraction_method": "failed",
            "rotation": 0,
            "processing_time": 0,
            "page_image_path": "",
            "embedded_images": []
        }

    def _detect_orientation_optimized(self, page) -> int:
        """Optimized orientation detection"""
        try:
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])
            
            if not blocks:
                return 0
            
            for block in blocks[:2]:
                if block.get("type") == 0 and block.get("lines"):
                    line = block["lines"][0]
                    if "dir" in line and isinstance(line["dir"], (list, tuple)) and len(line["dir"]) >= 2:
                        x, y = line["dir"][0], line["dir"][1]
                        if abs(x) > abs(y):
                            return 180 if x < 0 else 0
                        else:
                            return 90 if y > 0 else 270
            
            return 0
            
        except Exception:
            return 0

    def _extract_text_optimized(self, page) -> Tuple[str, str]:
        """Optimized text extraction"""
        try:
            text = page.get_text("text")
            if text and text.strip():
                return text.strip(), "text"
        except Exception:
            pass
        
        try:
            text_dict = page.get_text("dict")
            content = ""
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            if span_text.strip():
                                content += span_text + " "
                        content += "\n"
            
            if content.strip():
                return content.strip(), "dict"
        except Exception:
            pass
        
        return "", "none"

    def _extract_embedded_images_optimized(self, doc, page, page_num: int, images_folder: str) -> List[Dict]:
        """Optimized image extraction"""
        page_images = []
        
        try:
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    if isinstance(img, (tuple, list)) and len(img) > 0:
                        xref = img[0]
                    else:
                        continue
                    
                    if not isinstance(xref, int) or xref <= 0:
                        continue
                    
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    if not image_bytes or not image_ext or len(image_bytes) < 2048:
                        continue
                    
                    image_filename = f"page{page_num+1}image{img_index}.{image_ext}"
                    image_path = os.path.join(images_folder, image_filename)
                    
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
                    
                except Exception as e:
                    self.logger.debug(f"Error extracting image {img_index}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error getting images: {e}")
        
        return page_images

    def _render_page_image_optimized(self, page_num: int, rotation: int, output_folder: str) -> str:
        """CORRECTED: Optimized page image rendering with proper list handling"""
        try:
            images = convert_from_path(
                self.pdf_path,
                dpi=150,
                first_page=page_num+1,
                last_page=page_num+1
            )
            
            if images and len(images) > 0:
                img = images[0]  # CORRECTED: Get first image from list
                
                if rotation != 0:
                    img = img.rotate(rotation, expand=True)
                
                image_filename = f"page_{page_num + 1:03d}.png"
                image_path = os.path.join(output_folder, image_filename)
                img.save(image_path)  # Now calling save() on PIL Image object
                
                return image_path
            else:
                return ""
                
        except Exception as e:
            self.logger.error(f"Error rendering page {page_num+1}: {e}")
            return ""

    async def _store_text_and_images_only(self, page_results: List[Dict], skip_image_extraction: bool = False):
        """✅ UPDATED: Store page-wise text chunks in DocumentChunk + images (NO PageText)"""
    
        # Prepare text chunks and image tasks
        text_chunks = []
        image_tasks = []
    
        self.logger.info("🔥 Phase 1: Processing page-wise text chunks + image storage (NO PageText)")
    
        for page_data in page_results:
            page_content = page_data.get("page_content", "")
        
            # ✅ NEW: Store entire page text as single chunk in DocumentChunk
            if page_content and page_content.strip():
                try:
                    chunk_text = page_content.strip()
                    embedding = self.embedding_model.encode(chunk_text).tolist()

                    chunk_doc = DocumentChunk(
                        document_id=str(self.pdf_record.id),
                        page_number=page_data["page"],
                        chunk_index=0,  # Always 0 for page-wise chunks
                        content_type='text',
                        content=chunk_text,
                        embedding=embedding,
                        metadata={
                            'filename': self.pdf_record.filename,
                            'source': 'page_text_full',
                            'word_count': len(chunk_text.split()),
                            'char_count': len(chunk_text),
                            'phase': 'phase_1_page_wise',
                            'chunking_strategy': 'page_wise'
                        }
                    )
                    text_chunks.append(chunk_doc)

                    self.logger.info(f"📝 Page {page_data['page']}: Stored as single chunk ({len(chunk_text)} chars)")

                except Exception as e:
                    self.logger.error(f"❌ Error storing page {page_data['page']} as chunk: {e}")

            # ✅ UNCHANGED: Image processing remains exactly the same
            if not skip_image_extraction:
                for img_data in page_data.get("embedded_images", []):
                    img_path = os.path.join(
                        self.temp_folder, 
                        "embedded_images", 
                        f"page{page_data['page']}image{img_data['index']}.{img_data['extension']}"
                    )

                    if os.path.exists(img_path):
                        task = self._upload_single_image_optimized(img_path, page_data['page'], img_data['index'])
                        image_tasks.append(task)

        # ✅ UPDATED: Execute storage tasks (NO PageText storage)
        try:
            if skip_image_extraction:
                # Large PDFs: Store text chunks only
                self.logger.info(f"⚠️ Large PDF - storing PAGE-WISE TEXT CHUNKS ONLY (no images)")
                await self._store_text_chunks_batch(text_chunks)
                self.logger.info(f"✅ {len(text_chunks)} page-wise text chunks stored successfully (images skipped)")
            else:
                # Normal PDFs: Store text chunks + images
                storage_tasks = [
                    self._store_text_chunks_batch(text_chunks),
                    self._store_images_batch(image_tasks)
                ]
                await asyncio.gather(*storage_tasks, return_exceptions=True)
                self.logger.info(f"✅ {len(text_chunks)} page-wise text chunks + images stored successfully")

        except Exception as e:
            self.logger.error(f"Error in page-wise data storage: {e}")


    async def _store_text_chunks_batch(self, text_chunks: List[DocumentChunk]):
        """✅ NEW: Store page-wise text chunks in batch"""
        if not text_chunks:
            self.logger.info("No page-wise text chunks to store")
            return
    
        try:
            await DocumentChunk.insert_many(text_chunks)
            self.logger.info(f"✅ Phase 1: Batch inserted {len(text_chunks)} page-wise text chunks")
        except AttributeError:
        # Fallback to individual inserts
            insert_tasks = [chunk.insert() for chunk in text_chunks]
            await asyncio.gather(*insert_tasks, return_exceptions=True)
            self.logger.info(f"✅ Phase 1: Individually inserted {len(text_chunks)} page-wise text chunks")
        except Exception as e:
            self.logger.error(f"Error storing page-wise text chunks: {e}")



    # async def _store_page_texts_batch(self, page_texts: List[PageText]):
    #     """Store page texts in batch"""
    #     if not page_texts:
    #         return
        
    #     try:
    #         await PageText.insert_many(page_texts)
    #         self.logger.info(f"✅ Batch inserted {len(page_texts)} page texts")
    #     except AttributeError:
    #         # Fallback to individual inserts
    #         insert_tasks = [text.insert() for text in page_texts]
    #         await asyncio.gather(*insert_tasks, return_exceptions=True)
    #         self.logger.info(f"✅ Individually inserted {len(page_texts)} page texts")
    #     except Exception as e:
    #         self.logger.error(f"Error storing page texts: {e}")

    async def _store_images_batch(self, image_tasks: List):
        """Store images with controlled concurrency"""
        if not image_tasks:
            return
        
        semaphore = asyncio.Semaphore(6)  # Reduced from 8 to 6 for stability
        
        async def upload_with_semaphore(task):
            async with semaphore:
                return await task
        
        self.logger.info(f"Uploading {len(image_tasks)} images...")
        
        try:
            results = await asyncio.gather(
                *[upload_with_semaphore(task) for task in image_tasks],
                return_exceptions=True
            )
            
            # Store image records
            image_records = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.debug(f"Image upload error: {result}")
                elif result:
                    image_record = ImageModel(
                        pdf_id=self.pdf_record.id,
                        page_number=result["page_number"],
                        cloudinary_url=result["cloudinary_url"]
                    )
                    image_records.append(image_record)
            
            if image_records:
                try:
                    await ImageModel.insert_many(image_records)
                    self.logger.info(f"✅ Batch inserted {len(image_records)} image records")
                except AttributeError:
                    insert_tasks = [record.insert() for record in image_records]
                    await asyncio.gather(*insert_tasks, return_exceptions=True)
                    self.logger.info(f"✅ Individually inserted {len(image_records)} image records")
        except Exception as e:
            self.logger.error(f"Error in image storage: {e}")

    async def _upload_single_image_optimized(self, img_path: str, page_num: int, img_index: int) -> Optional[Dict]:
        """Upload single image"""
        try:
            with open(img_path, 'rb') as img_file:
                image_data = img_file.read()
            
            upload_result = await storage_service.upload_image(
                image_data=image_data,
                folder=f"pdf_images/pdf_{self.pdf_record.id}",
                public_id=f"page_{page_num}_img_{img_index}",
                max_retries=1
            )
            
            return {
                "page_number": page_num,
                "cloudinary_url": upload_result["url"]
            }
            
        except Exception as e:
            self.logger.debug(f"Error uploading image: {e}")
            return None

    def _cleanup_files(self):
        """Cleanup temporary files"""
        try:
            if os.path.exists(self.temp_folder):
                shutil.rmtree(self.temp_folder)
                self.logger.info(f"✅ Cleaned up temporary folder")
        except Exception as e:
            self.logger.error(f"Error cleaning up: {e}")


# Enhanced wrapper function
async def process_pdf_phase_1_async(pdf_path: str, filename: str, user_id: str) -> Dict[str, Any]:
    """🔥 ENHANCED: Process PDF/Word/Spreadsheet files"""
    processor = StreamlinedPDFProcessor(pdf_path, user_id)
    return await processor.process_pdf_phase_1(filename)
