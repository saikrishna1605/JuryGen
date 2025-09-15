"""
Storage service for handling file uploads and downloads using Google Cloud Storage.
"""

import os
import io
from typing import Optional, Tuple
from datetime import datetime, timedelta

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    GOOGLE_CLOUD_STORAGE_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_STORAGE_AVAILABLE = False
    print("Google Cloud Storage not available. Using mock storage service.")


class StorageService:
    """Service for file storage operations using Google Cloud Storage."""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.bucket_name = os.getenv("STORAGE_BUCKET_NAME")
        
        if GOOGLE_CLOUD_STORAGE_AVAILABLE and self.project_id and self.bucket_name:
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            self.enabled = True
        else:
            self.client = None
            self.bucket = None
            self.enabled = False
            print("Google Cloud Storage not configured. Using mock storage.")
    
    async def generate_signed_upload_url(
        self,
        blob_name: str,
        content_type: str,
        expires_in: int = 3600
    ) -> Tuple[str, datetime]:
        """
        Generate a signed URL for uploading a file.
        
        Args:
            blob_name: Name/path of the blob in storage
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Tuple of (signed_url, expiration_datetime)
        """
        if not self.enabled:
            return await self._mock_signed_upload_url(blob_name, expires_in)
        
        try:
            blob = self.bucket.blob(blob_name)
            
            # Generate signed URL for upload
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_in),
                method="PUT",
                content_type=content_type,
                headers={"Content-Type": content_type}
            )
            
            expiration = datetime.utcnow() + timedelta(seconds=expires_in)
            return url, expiration
            
        except Exception as e:
            print(f"Failed to generate signed upload URL: {str(e)}")
            return await self._mock_signed_upload_url(blob_name, expires_in)
    
    async def generate_signed_download_url(
        self,
        blob_name: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a signed URL for downloading a file.
        
        Args:
            blob_name: Name/path of the blob in storage
            expires_in: URL expiration time in seconds
            
        Returns:
            Signed download URL
        """
        if not self.enabled:
            return f"https://mock-storage.example.com/download/{blob_name}?expires={expires_in}"
        
        try:
            blob = self.bucket.blob(blob_name)
            
            # Check if blob exists
            if not blob.exists():
                raise FileNotFoundError(f"File not found: {blob_name}")
            
            # Generate signed URL for download
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_in),
                method="GET"
            )
            
            return url
            
        except Exception as e:
            print(f"Failed to generate signed download URL: {str(e)}")
            raise
    
    async def upload_file(
        self,
        blob_name: str,
        file_content: bytes,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file directly to storage.
        
        Args:
            blob_name: Name/path of the blob in storage
            file_content: File content as bytes
            content_type: MIME type of the file
            metadata: Optional metadata dictionary
            
        Returns:
            True if upload successful, False otherwise
        """
        if not self.enabled:
            print(f"Mock upload: {blob_name} ({len(file_content)} bytes)")
            return True
        
        try:
            blob = self.bucket.blob(blob_name)
            
            # Set content type
            blob.content_type = content_type
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            
            # Upload the file
            blob.upload_from_string(file_content)
            
            return True
            
        except Exception as e:
            print(f"Failed to upload file: {str(e)}")
            return False
    
    async def download_file(self, blob_name: str) -> bytes:
        """
        Download a file from storage.
        
        Args:
            blob_name: Name/path of the blob in storage
            
        Returns:
            File content as bytes
        """
        if not self.enabled:
            return await self._mock_download_file(blob_name)
        
        try:
            blob = self.bucket.blob(blob_name)
            
            # Check if blob exists
            if not blob.exists():
                raise FileNotFoundError(f"File not found: {blob_name}")
            
            # Download the file
            content = blob.download_as_bytes()
            return content
            
        except Exception as e:
            print(f"Failed to download file: {str(e)}")
            raise
    
    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            blob_name: Name/path of the blob in storage
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.enabled:
            print(f"Mock delete: {blob_name}")
            return True
        
        try:
            blob = self.bucket.blob(blob_name)
            
            # Check if blob exists
            if not blob.exists():
                return True  # Already deleted
            
            # Delete the file
            blob.delete()
            return True
            
        except Exception as e:
            print(f"Failed to delete file: {str(e)}")
            return False
    
    async def file_exists(self, blob_name: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            blob_name: Name/path of the blob in storage
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.enabled:
            return True  # Mock always returns True
        
        try:
            blob = self.bucket.blob(blob_name)
            return blob.exists()
            
        except Exception as e:
            print(f"Failed to check file existence: {str(e)}")
            return False
    
    async def get_file_metadata(self, blob_name: str) -> Optional[dict]:
        """
        Get metadata for a file in storage.
        
        Args:
            blob_name: Name/path of the blob in storage
            
        Returns:
            File metadata dictionary or None if not found
        """
        if not self.enabled:
            return {
                "name": blob_name,
                "size": 1024,
                "content_type": "application/octet-stream",
                "created": datetime.utcnow().isoformat(),
                "updated": datetime.utcnow().isoformat()
            }
        
        try:
            blob = self.bucket.blob(blob_name)
            
            # Reload to get latest metadata
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "etag": blob.etag,
                "metadata": blob.metadata or {}
            }
            
        except NotFound:
            return None
        except Exception as e:
            print(f"Failed to get file metadata: {str(e)}")
            return None
    
    async def list_files(
        self,
        prefix: str = "",
        max_results: int = 100
    ) -> list:
        """
        List files in storage with optional prefix filter.
        
        Args:
            prefix: Prefix to filter files
            max_results: Maximum number of results to return
            
        Returns:
            List of file information dictionaries
        """
        if not self.enabled:
            return [
                {
                    "name": f"{prefix}sample_file_1.pdf",
                    "size": 1024,
                    "content_type": "application/pdf",
                    "created": datetime.utcnow().isoformat()
                },
                {
                    "name": f"{prefix}sample_file_2.docx",
                    "size": 2048,
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "created": datetime.utcnow().isoformat()
                }
            ]
        
        try:
            blobs = self.client.list_blobs(
                self.bucket,
                prefix=prefix,
                max_results=max_results
            )
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "etag": blob.etag
                })
            
            return files
            
        except Exception as e:
            print(f"Failed to list files: {str(e)}")
            return []
    
    async def _mock_signed_upload_url(self, blob_name: str, expires_in: int) -> Tuple[str, datetime]:
        """Mock signed upload URL for development."""
        url = f"https://mock-storage.example.com/upload/{blob_name}?expires={expires_in}"
        expiration = datetime.utcnow() + timedelta(seconds=expires_in)
        return url, expiration
    
    async def _mock_download_file(self, blob_name: str) -> bytes:
        """Mock file download for development."""
        # Return sample PDF content
        sample_content = b"""
        %PDF-1.4
        1 0 obj
        <<
        /Type /Catalog
        /Pages 2 0 R
        >>
        endobj
        
        2 0 obj
        <<
        /Type /Pages
        /Kids [3 0 R]
        /Count 1
        >>
        endobj
        
        3 0 obj
        <<
        /Type /Page
        /Parent 2 0 R
        /MediaBox [0 0 612 792]
        >>
        endobj
        
        xref
        0 4
        0000000000 65535 f 
        0000000009 00000 n 
        0000000074 00000 n 
        0000000120 00000 n 
        trailer
        <<
        /Size 4
        /Root 1 0 R
        >>
        startxref
        179
        %%EOF
        """
        return sample_content.strip()