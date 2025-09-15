"""
Document service for handling document operations and database interactions.
"""

import os
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models.document import Document, ProcessedDocument, DocumentMetadata, OCRResult
from ..core.database import Base, engine
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean


class DocumentModel(Base):
    """SQLAlchemy model for documents table."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, default=0)
    processing_status = Column(String, default="pending_upload")
    user_id = Column(String, nullable=False, index=True)
    jurisdiction = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    storage_url = Column(String, nullable=True)
    structured_text = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OCRResultModel(Base):
    """SQLAlchemy model for OCR results table."""
    __tablename__ = "ocr_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    layout = Column(JSON, nullable=True)
    processing_method = Column(String, nullable=False)
    language_code = Column(String, default="en")
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentService:
    """Service class for document operations."""
    
    def __init__(self):
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
    
    async def create_document(self, db: Session, document_data: Dict[str, Any]) -> DocumentModel:
        """Create a new document record."""
        document = DocumentModel(**document_data)
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    
    async def get_document(self, db: Session, document_id: str, user_id: str) -> Optional[DocumentModel]:
        """Get a document by ID and user ID."""
        return db.query(DocumentModel).filter(
            and_(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id
            )
        ).first()
    
    async def update_document(self, db: Session, document_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a document record."""
        result = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).update(update_data)
        db.commit()
        return result > 0
    
    async def delete_document(self, db: Session, document_id: str) -> bool:
        """Delete a document and its related records."""
        # Delete OCR results first
        db.query(OCRResultModel).filter(
            OCRResultModel.document_id == document_id
        ).delete()
        
        # Delete document
        result = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).delete()
        
        db.commit()
        return result > 0
    
    async def get_user_documents(
        self,
        db: Session,
        user_id: str,
        page: int = 1,
        per_page: int = 10,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated list of user documents."""
        query = db.query(DocumentModel).filter(DocumentModel.user_id == user_id)
        
        if status_filter:
            query = query.filter(DocumentModel.processing_status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        documents = query.order_by(desc(DocumentModel.created_at)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        # Convert to dict format
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "content_type": doc.content_type,
                "size_bytes": doc.size_bytes,
                "processing_status": doc.processing_status,
                "user_id": doc.user_id,
                "jurisdiction": doc.jurisdiction,
                "user_role": doc.user_role,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "processing_time": doc.processing_time,
                "error_message": doc.error_message
            })
        
        return document_list, total
    
    async def get_processed_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
        include_analysis: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get a processed document with analysis results."""
        document = await self.get_document(db, document_id, user_id)
        if not document:
            return None
        
        result = {
            "id": document.id,
            "filename": document.filename,
            "content_type": document.content_type,
            "size_bytes": document.size_bytes,
            "processing_status": document.processing_status,
            "user_id": document.user_id,
            "jurisdiction": document.jurisdiction,
            "user_role": document.user_role,
            "storage_url": document.storage_url,
            "structured_text": document.structured_text,
            "metadata": document.metadata,
            "processing_time": document.processing_time,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "error_message": document.error_message
        }
        
        if include_analysis:
            # Get OCR results
            ocr_result = db.query(OCRResultModel).filter(
                OCRResultModel.document_id == document_id
            ).first()
            
            if ocr_result:
                result["ocr_result"] = {
                    "text": ocr_result.text,
                    "confidence": ocr_result.confidence,
                    "layout": ocr_result.layout,
                    "processing_method": ocr_result.processing_method,
                    "language_code": ocr_result.language_code,
                    "processing_time": ocr_result.processing_time
                }
            
            # TODO: Add clauses, risk assessment, etc.
            result["clauses"] = []
            result["risk_assessment"] = None
            result["summary"] = None
        
        return result
    
    async def store_ocr_result(self, db: Session, document_id: str, ocr_result: OCRResult) -> bool:
        """Store OCR processing result."""
        ocr_model = OCRResultModel(
            document_id=document_id,
            text=ocr_result.text,
            confidence=ocr_result.confidence,
            layout=ocr_result.layout.dict() if ocr_result.layout else None,
            processing_method=ocr_result.processing_method,
            language_code=ocr_result.language_code,
            processing_time=ocr_result.processing_time
        )
        
        db.add(ocr_model)
        db.commit()
        return True
    
    async def get_processing_progress(self, db: Session, document_id: str) -> Optional[Dict[str, Any]]:
        """Get processing progress for a document."""
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
        
        if not document:
            return None
        
        # Calculate progress based on status
        progress_map = {
            "pending_upload": 0,
            "queued": 10,
            "processing": 50,
            "completed": 100,
            "failed": 0
        }
        
        return {
            "percentage": progress_map.get(document.processing_status, 0),
            "status": document.processing_status,
            "error_message": document.error_message,
            "processing_time": document.processing_time
        }
    
    async def extract_metadata(self, file_content: bytes, content_type: str) -> Optional[DocumentMetadata]:
        """Extract metadata from document file."""
        try:
            metadata = DocumentMetadata()
            
            if content_type == "application/pdf":
                # Use PyPDF2 or similar to extract PDF metadata
                metadata.page_count = 1  # Placeholder
                metadata.word_count = len(file_content.decode('utf-8', errors='ignore').split())
                
            elif content_type.startswith("application/vnd.openxmlformats"):
                # Use python-docx to extract DOCX metadata
                metadata.word_count = len(file_content.decode('utf-8', errors='ignore').split())
                
            elif content_type.startswith("image/"):
                # Image metadata extraction
                metadata.page_count = 1
                
            metadata.character_count = len(file_content)
            metadata.creation_date = datetime.utcnow()
            
            return metadata
            
        except Exception as e:
            print(f"Failed to extract metadata: {str(e)}")
            return None