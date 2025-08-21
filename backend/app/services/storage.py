"""
Google Cloud Storage service for file operations.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from urllib.parse import urlparse

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, NotFound
from google.api_core import exceptions as gcp_exceptions

from app.core.config import settings
import structlog

logger = structlog.get_logger()


class StorageService:
    """Service for Google Cloud Storage operations."""
    
    def __init__(self):
        """Initialize the storage service."""
        self.client = storage.Client()
        self.bucket_name = settings.STORAGE_BUCKET
        self.bucket = self.client.bucket(self.bucket_name)
    
    async def generate_signed_upload_url(
        self,
        blob_name: str,
        content_type: str,
        size_limit: int,
        expiration_minutes: int = 30
    ) -> str:
        """
        Generate a signed URL for uploading a file.
        
        Args:
            blob_name: Name of the blob in the bucket
            content_type: MIME type of the file
            size_limit: Maximum file size in bytes
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed upload URL
        """
        try:
            blob = self.bucket.blob(blob_name)
            
            # Set conditions for the upload
            conditions = [
                ["content-length-range", 1, size_limit],
                ["eq", "$Content-Type", content_type],
            ]
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(minutes=expiration_minutes),
                method="PUT",
                content_type=content_type,
                conditions=conditions,
            )
            
            logger.info(
                "Generated signed upload URL",
                blob_name=blob_name,
                content_type=content_type,
                size_limit=size_limit,
                expiration_minutes=expiration_minutes
            )
            
            return url
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to generate signed upload URL",
                blob_name=blob_name,
                error=str(e)
            )
            raise
    
    async def generate_signed_download_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60
    ) -> str:
        """
        Generate a signed URL for downloading a file.
        
        Args:
            blob_name: Name of the blob in the bucket
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed download URL
        """
        try:
            blob = self.bucket.blob(blob_name)
            
            # Check if blob exists
            if not blob.exists():
                raise NotFound(f"Blob {blob_name} not found")
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(minutes=expiration_minutes),
                method="GET",
            )
            
            logger.info(
                "Generated signed download URL",
                blob_name=blob_name,
                expiration_minutes=expiration_minutes
            )
            
            return url
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to generate signed download URL",
                blob_name=blob_name,
                error=str(e)
            )
            raise
    
    async def blob_exists(self, storage_url: str) -> bool:
        """
        Check if a blob exists in storage.
        
        Args:
            storage_url: Full storage URL (gs://bucket/path)
            
        Returns:
            True if blob exists, False otherwise
        """
        try:
            blob_name = self._extract_blob_name(storage_url)
            blob = self.bucket.blob(blob_name)
            return blob.exists()
            
        except Exception as e:
            logger.error(
                "Error checking blob existence",
                storage_url=storage_url,
                error=str(e)
            )
            return False
    
    async def get_blob_metadata(self, storage_url: str) -> Optional[dict]:
        """
        Get metadata for a blob.
        
        Args:
            storage_url: Full storage URL (gs://bucket/path)
            
        Returns:
            Blob metadata dictionary or None if not found
        """
        try:
            blob_name = self._extract_blob_name(storage_url)
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                return None
            
            # Reload to get latest metadata
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created,
                "updated": blob.updated,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
                "etag": blob.etag,
                "generation": blob.generation,
                "metageneration": blob.metageneration,
                "custom_metadata": blob.metadata or {},
            }
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get blob metadata",
                storage_url=storage_url,
                error=str(e)
            )
            return None
    
    async def upload_file(
        self,
        file_obj: BinaryIO,
        blob_name: str,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file directly to storage.
        
        Args:
            file_obj: File object to upload
            blob_name: Name of the blob in the bucket
            content_type: MIME type of the file
            metadata: Optional custom metadata
            
        Returns:
            Storage URL of the uploaded file
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.content_type = content_type
            
            if metadata:
                blob.metadata = metadata
            
            # Upload the file
            blob.upload_from_file(file_obj, rewind=True)
            
            storage_url = f"gs://{self.bucket_name}/{blob_name}"
            
            logger.info(
                "File uploaded successfully",
                blob_name=blob_name,
                content_type=content_type,
                size=blob.size
            )
            
            return storage_url
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to upload file",
                blob_name=blob_name,
                error=str(e)
            )
            raise
    
    async def download_file(self, storage_url: str) -> bytes:
        """
        Download a file from storage.
        
        Args:
            storage_url: Full storage URL (gs://bucket/path)
            
        Returns:
            File content as bytes
        """
        try:
            blob_name = self._extract_blob_name(storage_url)
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                raise NotFound(f"File not found: {storage_url}")
            
            content = blob.download_as_bytes()
            
            logger.info(
                "File downloaded successfully",
                storage_url=storage_url,
                size=len(content)
            )
            
            return content
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to download file",
                storage_url=storage_url,
                error=str(e)
            )
            raise
    
    async def delete_file(self, storage_url: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            storage_url: Full storage URL (gs://bucket/path)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            blob_name = self._extract_blob_name(storage_url)
            blob = self.bucket.blob(blob_name)
            
            if blob.exists():
                blob.delete()
                logger.info("File deleted successfully", storage_url=storage_url)
                return True
            else:
                logger.warning("File not found for deletion", storage_url=storage_url)
                return False
                
        except GoogleCloudError as e:
            logger.error(
                "Failed to delete file",
                storage_url=storage_url,
                error=str(e)
            )
            return False
    
    async def copy_file(
        self,
        source_url: str,
        destination_blob_name: str,
        destination_bucket: Optional[str] = None
    ) -> str:
        """
        Copy a file within or between buckets.
        
        Args:
            source_url: Source storage URL
            destination_blob_name: Destination blob name
            destination_bucket: Destination bucket (defaults to same bucket)
            
        Returns:
            Destination storage URL
        """
        try:
            source_blob_name = self._extract_blob_name(source_url)
            source_blob = self.bucket.blob(source_blob_name)
            
            if not source_blob.exists():
                raise NotFound(f"Source file not found: {source_url}")
            
            # Determine destination bucket
            dest_bucket = self.bucket
            if destination_bucket and destination_bucket != self.bucket_name:
                dest_bucket = self.client.bucket(destination_bucket)
            
            # Copy the blob
            dest_blob = dest_bucket.copy_blob(source_blob, dest_bucket, destination_blob_name)
            
            dest_url = f"gs://{dest_bucket.name}/{destination_blob_name}"
            
            logger.info(
                "File copied successfully",
                source_url=source_url,
                destination_url=dest_url
            )
            
            return dest_url
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to copy file",
                source_url=source_url,
                destination_blob_name=destination_blob_name,
                error=str(e)
            )
            raise
    
    async def list_files(
        self,
        prefix: str = "",
        max_results: Optional[int] = None
    ) -> list[dict]:
        """
        List files in the bucket with optional prefix filter.
        
        Args:
            prefix: Prefix to filter files
            max_results: Maximum number of results
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            blobs = self.bucket.list_blobs(
                prefix=prefix,
                max_results=max_results
            )
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created,
                    "updated": blob.updated,
                    "storage_url": f"gs://{self.bucket_name}/{blob.name}",
                })
            
            logger.info(
                "Listed files successfully",
                prefix=prefix,
                count=len(files)
            )
            
            return files
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to list files",
                prefix=prefix,
                error=str(e)
            )
            raise
    
    def _extract_blob_name(self, storage_url: str) -> str:
        """
        Extract blob name from storage URL.
        
        Args:
            storage_url: Full storage URL (gs://bucket/path)
            
        Returns:
            Blob name (path within bucket)
        """
        if storage_url.startswith("gs://"):
            # Parse gs:// URL
            parsed = urlparse(storage_url)
            return parsed.path.lstrip("/")
        else:
            # Assume it's already a blob name
            return storage_url
    
    async def setup_bucket_lifecycle(self) -> None:
        """
        Set up bucket lifecycle rules for automatic cleanup.
        """
        try:
            # Define lifecycle rules
            lifecycle_rules = [
                {
                    "action": {"type": "Delete"},
                    "condition": {
                        "age": 30,  # Delete files older than 30 days
                        "matchesPrefix": ["documents/", "exports/"]
                    }
                },
                {
                    "action": {"type": "Delete"},
                    "condition": {
                        "age": 7,  # Delete temp files older than 7 days
                        "matchesPrefix": ["temp/"]
                    }
                }
            ]
            
            # Apply lifecycle rules
            self.bucket.lifecycle_rules = lifecycle_rules
            self.bucket.patch()
            
            logger.info("Bucket lifecycle rules configured successfully")
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to configure bucket lifecycle",
                error=str(e)
            )
            raise
    
    async def setup_bucket_cors(self) -> None:
        """
        Set up CORS configuration for the bucket.
        """
        try:
            cors_configuration = [
                {
                    "origin": settings.ALLOWED_ORIGINS,
                    "method": ["GET", "PUT", "POST", "DELETE", "OPTIONS"],
                    "responseHeader": [
                        "Content-Type",
                        "x-goog-resumable",
                        "x-goog-meta-*"
                    ],
                    "maxAgeSeconds": 3600
                }
            ]
            
            self.bucket.cors = cors_configuration
            self.bucket.patch()
            
            logger.info("Bucket CORS configuration updated successfully")
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to configure bucket CORS",
                error=str(e)
            )
            raise