import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Dict, Any, Union
from fastapi import UploadFile, HTTPException
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL")
)

logger = logging.getLogger(__name__)

class CloudinaryStorageService:
    """Service for handling document and image uploads to Cloudinary"""
    
    def __init__(self):
        # Verify Cloudinary configuration
        if not os.getenv("CLOUDINARY_URL"):
            raise ValueError("CLOUDINARY_URL not found in environment variables")
    
    async def upload_document(
        self, 
        file: UploadFile, 
        folder: str = "documents",
        public_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload document (PDF, DOC, etc.) to Cloudinary
        
        Args:
            file: FastAPI UploadFile object
            folder: Cloudinary folder to store the file
            public_id: Optional custom public_id
        
        Returns:
            Dict containing upload result with URL and metadata
        """
        try:
            # Read file content
            file_content = await file.read()
            
            # Reset file pointer for potential reuse
            await file.seek(0)
            
            # Upload parameters
            upload_params = {
                "resource_type": "raw",  # For non-image files like PDFs
                "folder": folder,
                "use_filename": True,
                "unique_filename": True,
                "overwrite": False,
            }
            
            if public_id:
                upload_params["public_id"] = public_id
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                **upload_params
            )
            
            logger.info(f"Document uploaded successfully: {result.get('public_id')}")
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "resource_type": result["resource_type"],
                "format": result.get("format"),
                "bytes": result.get("bytes"),
                "created_at": result.get("created_at"),
                "original_filename": file.filename
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to upload document: {str(e)}"
            )
    
    async def upload_image(
        self, 
        image_data: Union[bytes, UploadFile], 
        folder: str = "images",
        public_id: Optional[str] = None,
        transformation: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload image to Cloudinary
        
        Args:
            image_data: Image bytes or UploadFile object
            folder: Cloudinary folder to store the image
            public_id: Optional custom public_id
            transformation: Optional image transformations
        
        Returns:
            Dict containing upload result with URL and metadata
        """
        try:
            # Handle different input types
            if isinstance(image_data, UploadFile):
                content = await image_data.read()
                await image_data.seek(0)
                filename = image_data.filename
            else:
                content = image_data
                filename = None
            
            # Upload parameters
            upload_params = {
                "resource_type": "image",
                "folder": folder,
                "use_filename": True,
                "unique_filename": True,
                "overwrite": False,
            }
            
            if public_id:
                upload_params["public_id"] = public_id
            
            if transformation:
                upload_params["transformation"] = transformation
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                content,
                **upload_params
            )
            
            logger.info(f"Image uploaded successfully: {result.get('public_id')}")
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "resource_type": result["resource_type"],
                "format": result.get("format"),
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result.get("bytes"),
                "created_at": result.get("created_at"),
                "original_filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to upload image: {str(e)}"
            )
    
    def delete_file(self, public_id: str, resource_type: str = "raw") -> bool:
        """
        Delete file from Cloudinary
        
        Args:
            public_id: Cloudinary public_id of the file
            resource_type: Type of resource (raw, image, video)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = cloudinary.uploader.destroy(
                public_id, 
                resource_type=resource_type
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
    
    def get_file_info(self, public_id: str, resource_type: str = "raw") -> Optional[Dict]:
        """
        Get file information from Cloudinary
        
        Args:
            public_id: Cloudinary public_id of the file
            resource_type: Type of resource (raw, image, video)
        
        Returns:
            File information dict or None if not found
        """
        try:
            result = cloudinary.api.resource(
                public_id, 
                resource_type=resource_type
            )
            return result
            
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
        expiration: int = 3600
    ) -> str:
        """
        Generate signed URL for secure access
        
        Args:
            public_id: Cloudinary public_id
            resource_type: Type of resource
            expiration: URL expiration time in seconds
        
        Returns:
            Signed URL string
        """
        try:
            signed_url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                sign_url=True,
                type="authenticated",
                expires_at=expiration
            )[0]
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {public_id}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate signed URL: {str(e)}"
            )

# Create singleton instance
storage_service = CloudinaryStorageService()
