import os
import ssl
import certifi
import urllib3
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Dict, Any, Union, List
from fastapi import UploadFile, HTTPException
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CloudinaryStorageService:
    """
    Enhanced service for handling document and image uploads to Cloudinary 
    with SSL fixes, validation, and performance optimizations
    """
    
    # Allowed document types for processing
    ALLOWED_DOCUMENT_TYPES = {
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages','csv', 'xls', 'xlsx','png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'svg'
    }
    
    # Allowed image types
    ALLOWED_IMAGE_TYPES = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg'
    }
    
    # Blocked file types (security)
    BLOCKED_TYPES = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 
        'jar', 'app', 'deb', 'pkg', 'dmg', 'rpm', 'msi'
    }
    
    def __init__(self):
        """Initialize with robust SSL configuration and connection testing"""
        # Verify Cloudinary configuration
        if not os.getenv("CLOUDINARY_URL"):
            raise ValueError("CLOUDINARY_URL not found in environment variables")
        
        # FIXED: Configure SSL properly for macOS and handle connection issues
        self._configure_ssl_and_connection()
        
        # Initialize thread pool for async operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cloudinary_upload")
        
        logger.info("CloudinaryStorageService initialized successfully")
    
    def _configure_ssl_and_connection(self):
        """Configure SSL and test Cloudinary connection with retry logic"""
        # Disable SSL warnings for development
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Try multiple SSL configurations
        ssl_configs = [
            # Primary: Standard secure configuration
            {
                "secure": True,
                "ssl_verify": True,
                "timeout": 30
            },
            # Fallback 1: Relaxed SSL for macOS issues
            {
                "secure": True,
                "ssl_verify": False,
                "timeout": 30
            },
            # Fallback 2: Basic configuration
            {
                "secure": False,
                "timeout": 30
            }
        ]
        
        for i, config in enumerate(ssl_configs):
            try:
                logger.info(f"Attempting Cloudinary connection with SSL config {i+1}/3...")
                
                # Configure cloudinary with current SSL settings
                cloudinary.config(
                    cloudinary_url=os.getenv("CLOUDINARY_URL"),
                    **config
                )
                
                # Test connection with timeout
                cloudinary.api.ping()
                
                if i == 0:
                    logger.info("Cloudinary connection verified with secure SSL")
                elif i == 1:
                    logger.warning("Cloudinary connected with relaxed SSL (development mode)")
                else:
                    logger.warning("Cloudinary connected with basic configuration")
                
                return  # Success, exit function
                
            except Exception as e:
                logger.error(f"SSL config {i+1} failed: {e}")
                if i == len(ssl_configs) - 1:
                    # All configurations failed
                    raise ValueError(f"All Cloudinary SSL configurations failed. Last error: {e}")
                continue
    
    def _validate_file_type(self, filename: str, allowed_types: set) -> bool:
        """Validate file type against allowed extensions"""
        if not filename:
            return False
        
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Check if blocked
        if file_ext in self.BLOCKED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' is not allowed for security reasons"
            )
        
        # Check if allowed
        return file_ext in allowed_types
    
    def _get_file_size_mb(self, content: bytes) -> float:
        """Get file size in MB"""
        return len(content) / (1024 * 1024)
    
    async def upload_document(
        self, 
        file: UploadFile, 
        folder: str = "documents",
        public_id: Optional[str] = None,
        max_size_mb: float = 50.0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Upload document with validation, size limits, and retry logic
        
        Args:
            file: FastAPI UploadFile object
            folder: Cloudinary folder to store the file
            public_id: Optional custom public_id
            max_size_mb: Maximum file size in MB
            max_retries: Maximum retry attempts for failed uploads
        
        Returns:
            Dict containing upload result with URL and metadata
        """
        # Validate file type
        if not self._validate_file_type(file.filename, self.ALLOWED_DOCUMENT_TYPES):
            raise HTTPException(
                status_code=400,
                detail=f"Document type not supported. Allowed types: {', '.join(self.ALLOWED_DOCUMENT_TYPES)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        file_size_mb = self._get_file_size_mb(file_content)
        if file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            )
        
        # Reset file pointer for potential reuse
        await file.seek(0)
        
        # Upload parameters
        upload_params = {
            "resource_type": "raw",  # For non-image files like PDFs
            "folder": folder,
            "use_filename": True,
            "unique_filename": True,
            "overwrite": False,
            "timeout": 60,  # Increased timeout for large files
            "context": {
                "original_filename": file.filename,
                "file_size_mb": round(file_size_mb, 2)
            }
        }
        
        if public_id:
            upload_params["public_id"] = public_id
        
        # OPTIMIZED: Upload with retry logic and proper error handling
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Uploading document (attempt {attempt + 1}/{max_retries}): {file.filename}")
                
                # Use thread pool for blocking upload operation
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_pool,
                    lambda: cloudinary.uploader.upload(file_content, **upload_params)
                )
                
                logger.info(f"Document uploaded successfully: {result.get('public_id')} ({file_size_mb:.1f}MB)")
                
                return {
                    "url": result["secure_url"],
                    "public_id": result["public_id"],
                    "resource_type": result["resource_type"],
                    "format": result.get("format"),
                    "bytes": result.get("bytes"),
                    "created_at": result.get("created_at"),
                    "original_filename": file.filename,
                    "file_size_mb": file_size_mb
                }
                
            except Exception as e:
                last_error = e
                logger.error(f"Upload attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                    logger.info(f"Retrying upload in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # All attempts failed
                    logger.error(f"All {max_retries} upload attempts failed for {file.filename}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Failed to upload document after {max_retries} attempts: {str(last_error)}"
                    )
    
    async def upload_image(
        self, 
        image_data: Union[bytes, UploadFile], 
        folder: str = "images",
        public_id: Optional[str] = None,
        transformation: Optional[Dict] = None,
        max_size_mb: float = 10.0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Upload image with validation, optimization, and retry logic
        
        Args:
            image_data: Image bytes or UploadFile object
            folder: Cloudinary folder to store the image
            public_id: Optional custom public_id
            transformation: Optional image transformations
            max_size_mb: Maximum file size in MB
            max_retries: Maximum retry attempts for failed uploads
        
        Returns:
            Dict containing upload result with URL and metadata
        """
        # Handle different input types
        if isinstance(image_data, UploadFile):
            # Validate file type for UploadFile
            if not self._validate_file_type(image_data.filename, self.ALLOWED_IMAGE_TYPES):
                raise HTTPException(
                    status_code=400,
                    detail=f"Image type not supported. Allowed types: {', '.join(self.ALLOWED_IMAGE_TYPES)}"
                )
            
            content = await image_data.read()
            await image_data.seek(0)
            filename = image_data.filename
        else:
            content = image_data
            filename = None
        
        # Validate file size
        file_size_mb = self._get_file_size_mb(content)
        if file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"Image size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            )
        
        # Upload parameters
        upload_params = {
            "resource_type": "image",
            "folder": folder,
            "use_filename": True,
            "unique_filename": True,
            "overwrite": False,
            "quality": "auto",  # Automatic quality optimization
            "fetch_format": "auto",  # Automatic format optimization
            "timeout": 60,  # Increased timeout
            "context": {
                "file_size_mb": round(file_size_mb, 2)
            }
        }
        
        if public_id:
            upload_params["public_id"] = public_id
        
        if transformation:
            upload_params["transformation"] = transformation
        else:
            # Default optimization transformation
            upload_params["transformation"] = [
                {"quality": "auto", "fetch_format": "auto"}
            ]
        
        if filename:
            upload_params["context"]["original_filename"] = filename
        
        # OPTIMIZED: Upload with retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.debug(f"Uploading image (attempt {attempt + 1}/{max_retries})")
                
                # Use thread pool for blocking upload operation
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_pool,
                    lambda: cloudinary.uploader.upload(content, **upload_params)
                )
                
                logger.info(f"Image uploaded successfully: {result.get('public_id')} ({file_size_mb:.1f}MB)")
                
                return {
                    "url": result["secure_url"],
                    "public_id": result["public_id"],
                    "resource_type": result["resource_type"],
                    "format": result.get("format"),
                    "width": result.get("width"),
                    "height": result.get("height"),
                    "bytes": result.get("bytes"),
                    "created_at": result.get("created_at"),
                    "original_filename": filename,
                    "file_size_mb": file_size_mb
                }
                
            except Exception as e:
                last_error = e
                logger.error(f"Image upload attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Wait before retry
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                    await asyncio.sleep(wait_time)
                else:
                    # All attempts failed
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Failed to upload image after {max_retries} attempts: {str(last_error)}"
                    )
    
    def delete_file(self, public_id: str, resource_type: str = "raw") -> bool:
        """
        Delete file from Cloudinary with enhanced error handling
        
        Args:
            public_id: Cloudinary public_id of the file
            resource_type: Type of resource (raw, image, video)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = cloudinary.uploader.destroy(
                public_id, 
                resource_type=resource_type,
                timeout=30
            )
            
            success = result.get("result") == "ok"
            if success:
                logger.info(f"File deleted successfully: {public_id}")
            else:
                logger.warning(f"File deletion failed: {public_id}, result: {result}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting file {public_id}: {str(e)}")
            return False
    
    async def delete_file_async(self, public_id: str, resource_type: str = "raw") -> bool:
        """Async version of delete_file"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            self.delete_file,
            public_id,
            resource_type
        )
    
    def get_file_info(self, public_id: str, resource_type: str = "raw") -> Optional[Dict]:
        """
        Get comprehensive file information from Cloudinary
        
        Args:
            public_id: Cloudinary public_id of the file
            resource_type: Type of resource (raw, image, video)
        
        Returns:
            File information dict or None if not found
        """
        try:
            result = cloudinary.api.resource(
                public_id, 
                resource_type=resource_type,
                type="upload",
                timeout=30
            )
            
            return {
                "public_id": result.get("public_id"),
                "version": result.get("version"),
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
                "resource_type": result.get("resource_type"),
                "created_at": result.get("created_at"),
                "bytes": result.get("bytes"),
                "type": result.get("type"),
                "url": result.get("url"),
                "secure_url": result.get("secure_url"),
                "folder": result.get("folder"),
                "context": result.get("context", {}),
                "metadata": result.get("metadata", {})
            }
            
        except cloudinary.exceptions.NotFound:
            logger.warning(f"File not found: {public_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting file info {public_id}: {str(e)}")
            return None
    
    def generate_signed_url(
        self, 
        public_id: str, 
        resource_type: str = "raw",
        expiration: int = 3600,
        transformation: Optional[Dict] = None
    ) -> str:
        """
        Generate signed URL for secure access with time-based expiration
        
        Args:
            public_id: Cloudinary public_id
            resource_type: Type of resource
            expiration: URL expiration time in seconds from now
            transformation: Optional transformations to apply
        
        Returns:
            Signed URL string
        """
        try:
            import time
            expire_at = int(time.time()) + expiration
            
            url_params = {
                "resource_type": resource_type,
                "type": "upload",
                "sign_url": True,
                "expires_at": expire_at
            }
            
            if transformation:
                url_params["transformation"] = transformation
            
            signed_url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                **url_params
            )
            
            logger.info(f"Generated signed URL for {public_id}, expires in {expiration} seconds")
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {public_id}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate signed URL: {str(e)}"
            )
    
    async def batch_delete(self, public_ids: List[str], resource_type: str = "raw") -> Dict[str, Any]:
        """
        Delete multiple files in batch operation with async processing
        
        Args:
            public_ids: List of Cloudinary public_ids to delete
            resource_type: Type of resource (raw, image, video)
        
        Returns:
            Summary of deletion results
        """
        if not public_ids:
            return {"deleted": 0, "failed": 0, "results": []}
        
        deleted_count = 0
        failed_count = 0
        results = []
        
        # Process in chunks to avoid API limits
        chunk_size = 100  # Cloudinary's bulk delete limit
        
        for i in range(0, len(public_ids), chunk_size):
            chunk = public_ids[i:i + chunk_size]
            
            try:
                # Use async thread pool for batch operations
                loop = asyncio.get_event_loop()
                
                if len(chunk) > 1:
                    result = await loop.run_in_executor(
                        self.thread_pool,
                        lambda: cloudinary.api.delete_resources(
                            chunk,
                            resource_type=resource_type,
                            type="upload",
                            timeout=60
                        )
                    )
                    
                    # Process results
                    deleted_items = result.get("deleted", {})
                    
                    for public_id in chunk:
                        if public_id in deleted_items and deleted_items[public_id] == "deleted":
                            deleted_count += 1
                            results.append({"public_id": public_id, "status": "deleted"})
                        else:
                            failed_count += 1
                            results.append({"public_id": public_id, "status": "failed"})
                else:
                    # Single file deletion
                    success = await self.delete_file_async(chunk[0], resource_type)
                    if success:
                        deleted_count += 1
                        results.append({"public_id": chunk[0], "status": "deleted"})
                    else:
                        failed_count += 1
                        results.append({"public_id": chunk[0], "status": "failed"})
                        
            except Exception as e:
                # Mark entire chunk as failed
                for public_id in chunk:
                    failed_count += 1
                    results.append({
                        "public_id": public_id, 
                        "status": "error", 
                        "error": str(e)
                    })
                logger.error(f"Batch delete error for chunk: {e}")
        
        logger.info(f"Batch deletion completed: {deleted_count} deleted, {failed_count} failed")
        
        return {
            "deleted": deleted_count,
            "failed": failed_count,
            "total": len(public_ids),
            "results": results
        }
    
    async def batch_upload_images(self, images: List[tuple], folder: str = "images") -> List[Dict[str, Any]]:
        """
        Upload multiple images in parallel for better performance
        
        Args:
            images: List of tuples (image_data, filename, public_id)
            folder: Cloudinary folder to store images
            
        Returns:
            List of upload results
        """
        async def upload_single_image(image_data, filename, public_id):
            try:
                # Create mock UploadFile object for image_data
                class MockUploadFile:
                    def __init__(self, data, filename):
                        self.data = data
                        self.filename = filename
                        
                    async def read(self):
                        return self.data
                        
                    async def seek(self, position):
                        pass
                
                if isinstance(image_data, bytes):
                    mock_file = MockUploadFile(image_data, filename)
                    return await self.upload_image(
                        image_data=mock_file,
                        folder=folder,
                        public_id=public_id
                    )
                else:
                    return await self.upload_image(
                        image_data=image_data,
                        folder=folder,
                        public_id=public_id
                    )
            except Exception as e:
                logger.error(f"Failed to upload image {filename}: {e}")
                return {"error": str(e), "filename": filename}
        
        # Process all uploads in parallel with semaphore to limit concurrent uploads
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent uploads
        
        async def upload_with_semaphore(image_data, filename, public_id):
            async with semaphore:
                return await upload_single_image(image_data, filename, public_id)
        
        tasks = [
            upload_with_semaphore(image_data, filename, public_id)
            for image_data, filename, public_id in images
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_upload_preset(self, preset_name: str) -> Optional[Dict]:
        """
        Get upload preset configuration
        
        Args:
            preset_name: Name of the upload preset
        
        Returns:
            Upload preset configuration or None if not found
        """
        try:
            result = cloudinary.api.upload_preset(preset_name)
            return result
        except cloudinary.exceptions.NotFound:
            logger.warning(f"Upload preset not found: {preset_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting upload preset {preset_name}: {str(e)}")
            return None
    
    def get_folder_contents(self, folder_path: str, max_results: int = 500) -> Dict[str, Any]:
        """
        Get contents of a folder in Cloudinary
        
        Args:
            folder_path: Path to the folder
            max_results: Maximum number of results to return
        
        Returns:
            Dictionary containing folder contents
        """
        try:
            result = cloudinary.api.resources(
                type="upload",
                prefix=folder_path,
                max_results=max_results,
                timeout=30
            )
            
            return {
                "total_count": result.get("total_count", 0),
                "resources": result.get("resources", []),
                "next_cursor": result.get("next_cursor"),
                "rate_limit_remaining": result.get("rate_limit_remaining")
            }
            
        except Exception as e:
            logger.error(f"Error getting folder contents for {folder_path}: {str(e)}")
            return {"total_count": 0, "resources": [], "error": str(e)}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get Cloudinary account usage statistics
        
        Returns:
            Dictionary containing usage statistics
        """
        try:
            result = cloudinary.api.usage(timeout=30)
            return {
                "plan": result.get("plan"),
                "last_updated": result.get("last_updated"),
                "objects": {
                    "usage": result.get("objects", {}).get("usage", 0),
                    "limit": result.get("objects", {}).get("limit", 0)
                },
                "bandwidth": {
                    "usage": result.get("bandwidth", {}).get("usage", 0),
                    "limit": result.get("bandwidth", {}).get("limit", 0)
                },
                "storage": {
                    "usage": result.get("storage", {}).get("usage", 0),
                    "limit": result.get("storage", {}).get("limit", 0)
                },
                "requests": {
                    "usage": result.get("requests", {}).get("usage", 0),
                    "limit": result.get("requests", {}).get("limit", 0)
                }
            }
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {"error": str(e)}
    
    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)

# Create singleton instance
storage_service = CloudinaryStorageService()
