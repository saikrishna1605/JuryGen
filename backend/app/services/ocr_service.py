"""
OCR service using Google Cloud Document AI for document processing.
"""

import os
import io
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from google.cloud import documentai
    from google.cloud import storage as gcs
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("Google Cloud libraries not available. Using mock OCR service.")

from ..models.document import OCRResult, DocumentLayout


class OCRService:
    """Service for OCR processing using Google Cloud Document AI."""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.location = os.getenv("DOCUMENT_AI_LOCATION", "us")
        self.processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        
        if GOOGLE_CLOUD_AVAILABLE and self.project_id and self.processor_id:
            self.client = documentai.DocumentProcessorServiceClient()
            self.processor_name = self.client.processor_path(
                self.project_id, self.location, self.processor_id
            )
            self.enabled = True
        else:
            self.client = None
            self.processor_name = None
            self.enabled = False
            print("Google Cloud Document AI not configured. Using mock OCR.")
    
    async def process_document(
        self,
        file_content: bytes,
        content_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> OCRResult:
        """
        Process document using Google Cloud Document AI.
        
        Args:
            file_content: Raw file content as bytes
            content_type: MIME type of the document
            options: Additional processing options
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        if not self.enabled:
            return await self._mock_ocr_processing(file_content, content_type, start_time)
        
        try:
            # Prepare the document for processing
            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type=content_type
            )
            
            # Configure the process request
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process the document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract text
            text = document.text
            
            # Calculate confidence score
            confidence = self._calculate_confidence(document)
            
            # Extract layout information
            layout = self._extract_layout(document)
            
            # Detect language
            language_code = self._detect_language(document) or "en"
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text,
                confidence=confidence,
                layout=layout,
                processing_method="document_ai",
                language_code=language_code,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"Document AI processing failed: {str(e)}")
            # Fallback to mock processing
            return await self._mock_ocr_processing(file_content, content_type, start_time)
    
    async def process_document_batch(
        self,
        documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> List[OCRResult]:
        """
        Process multiple documents in batch.
        
        Args:
            documents: List of documents with 'content' and 'content_type'
            options: Additional processing options
            
        Returns:
            List of OCRResult objects
        """
        results = []
        
        for doc in documents:
            result = await self.process_document(
                doc["content"],
                doc["content_type"],
                options
            )
            results.append(result)
        
        return results
    
    async def extract_tables(
        self,
        file_content: bytes,
        content_type: str
    ) -> List[Dict[str, Any]]:
        """
        Extract tables from document using specialized table extraction.
        
        Args:
            file_content: Raw file content as bytes
            content_type: MIME type of the document
            
        Returns:
            List of extracted tables with structure
        """
        if not self.enabled:
            return []
        
        try:
            # Use Document AI's table extraction capabilities
            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type=content_type
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            result = self.client.process_document(request=request)
            document = result.document
            
            tables = []
            for page in document.pages:
                for table in page.tables:
                    table_data = self._extract_table_data(table, document.text)
                    tables.append(table_data)
            
            return tables
            
        except Exception as e:
            print(f"Table extraction failed: {str(e)}")
            return []
    
    async def extract_form_fields(
        self,
        file_content: bytes,
        content_type: str
    ) -> Dict[str, str]:
        """
        Extract form fields from document.
        
        Args:
            file_content: Raw file content as bytes
            content_type: MIME type of the document
            
        Returns:
            Dictionary of field names and values
        """
        if not self.enabled:
            return {}
        
        try:
            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type=content_type
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            result = self.client.process_document(request=request)
            document = result.document
            
            form_fields = {}
            for page in document.pages:
                for form_field in page.form_fields:
                    field_name = self._get_text(form_field.field_name, document.text)
                    field_value = self._get_text(form_field.field_value, document.text)
                    form_fields[field_name] = field_value
            
            return form_fields
            
        except Exception as e:
            print(f"Form field extraction failed: {str(e)}")
            return {}
    
    def _calculate_confidence(self, document) -> float:
        """Calculate overall confidence score from document."""
        if not document.pages:
            return 0.0
        
        total_confidence = 0.0
        total_elements = 0
        
        for page in document.pages:
            for paragraph in page.paragraphs:
                if hasattr(paragraph, 'layout') and hasattr(paragraph.layout, 'confidence'):
                    total_confidence += paragraph.layout.confidence
                    total_elements += 1
        
        return total_confidence / total_elements if total_elements > 0 else 0.8
    
    def _extract_layout(self, document) -> DocumentLayout:
        """Extract layout information from document."""
        pages = []
        
        for i, page in enumerate(document.pages):
            page_info = {
                "page_number": i + 1,
                "width": page.dimension.width if hasattr(page, 'dimension') else 0,
                "height": page.dimension.height if hasattr(page, 'dimension') else 0,
                "paragraphs": len(page.paragraphs),
                "lines": len(page.lines) if hasattr(page, 'lines') else 0,
                "words": len(page.tokens) if hasattr(page, 'tokens') else 0
            }
            pages.append(page_info)
        
        return DocumentLayout(
            pages=pages,
            total_pages=len(document.pages)
        )
    
    def _detect_language(self, document) -> Optional[str]:
        """Detect document language."""
        # Simple language detection based on text content
        # In a real implementation, you might use Google Cloud Translation API
        text = document.text[:1000]  # Sample first 1000 characters
        
        # Basic language detection heuristics
        if any(char in text for char in "áéíóúñü"):
            return "es"
        elif any(char in text for char in "àâäéèêëïîôöùûüÿç"):
            return "fr"
        elif any(char in text for char in "äöüß"):
            return "de"
        else:
            return "en"
    
    def _extract_table_data(self, table, document_text: str) -> Dict[str, Any]:
        """Extract structured data from a table."""
        rows = []
        
        for row in table.body_rows:
            row_data = []
            for cell in row.cells:
                cell_text = self._get_text(cell.layout, document_text)
                row_data.append(cell_text)
            rows.append(row_data)
        
        # Extract header if available
        headers = []
        if table.header_rows:
            for cell in table.header_rows[0].cells:
                header_text = self._get_text(cell.layout, document_text)
                headers.append(header_text)
        
        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers) if headers else (len(rows[0]) if rows else 0)
        }
    
    def _get_text(self, layout, document_text: str) -> str:
        """Extract text from layout element."""
        if not layout or not layout.text_anchor:
            return ""
        
        text_segments = []
        for segment in layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else len(document_text)
            text_segments.append(document_text[start_index:end_index])
        
        return "".join(text_segments)
    
    async def _mock_ocr_processing(
        self,
        file_content: bytes,
        content_type: str,
        start_time: float
    ) -> OCRResult:
        """Mock OCR processing for development/testing."""
        
        # Simulate processing time
        processing_time = time.time() - start_time + 0.5
        
        # Generate mock text based on content type
        if content_type == "application/pdf":
            mock_text = """
            LEGAL DOCUMENT SAMPLE
            
            This is a sample legal document processed by the OCR service.
            
            TERMS AND CONDITIONS
            
            1. The parties agree to the following terms:
               - Payment shall be made within 30 days
               - All disputes shall be resolved through arbitration
               - This agreement is governed by state law
            
            2. Liability and Risk:
               - Each party assumes responsibility for their actions
               - Limitation of liability applies as per state regulations
            
            SIGNATURES
            
            Party A: _________________ Date: _________
            Party B: _________________ Date: _________
            """
        else:
            mock_text = "Sample document text extracted via OCR processing."
        
        # Create mock layout
        layout = DocumentLayout(
            pages=[{
                "page_number": 1,
                "width": 612,
                "height": 792,
                "paragraphs": 5,
                "lines": 15,
                "words": 50
            }],
            total_pages=1
        )
        
        return OCRResult(
            text=mock_text.strip(),
            confidence=0.95,
            layout=layout,
            processing_method="mock_ocr",
            language_code="en",
            processing_time=processing_time
        )