"""
Firestore database service for document and job management.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError, NotFound
from google.api_core import exceptions as gcp_exceptions

from app.core.config import settings
from app.models.document import Document, ProcessedDocument, Clause
from app.models.job import Job, JobProgress, JobResults
from app.models.user import User
import structlog

logger = structlog.get_logger()


class FirestoreService:
    """Service for Firestore database operations."""
    
    def __init__(self):
        """Initialize the Firestore service."""
        self.client = firestore.Client()
        
        # Collection references
        self.users_collection = self.client.collection("users")
        self.documents_collection = self.client.collection("documents")
        self.jobs_collection = self.client.collection("jobs")
        self.clauses_collection = self.client.collection("clauses")
        self.results_collection = self.client.collection("results")
    
    # User operations
    async def create_user(self, user: User) -> None:
        """Create a new user document."""
        try:
            user_dict = user.model_dump(mode="json")
            user_dict["created_at"] = firestore.SERVER_TIMESTAMP
            user_dict["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.users_collection.document(user.id).set(user_dict)
            
            logger.info("User created successfully", user_id=user.id)
            
        except GoogleCloudError as e:
            logger.error("Failed to create user", user_id=user.id, error=str(e))
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            doc = await self.users_collection.document(user_id).get()
            
            if not doc.exists:
                return None
            
            user_data = doc.to_dict()
            return User(**user_data)
            
        except GoogleCloudError as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            raise
    
    async def update_user(self, user: User) -> None:
        """Update an existing user."""
        try:
            user_dict = user.model_dump(mode="json", exclude={"id", "created_at"})
            user_dict["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.users_collection.document(user.id).update(user_dict)
            
            logger.info("User updated successfully", user_id=user.id)
            
        except GoogleCloudError as e:
            logger.error("Failed to update user", user_id=user.id, error=str(e))
            raise
    
    # Document operations
    async def create_document(self, document: Document) -> None:
        """Create a new document record."""
        try:
            doc_dict = document.model_dump(mode="json")
            doc_dict["created_at"] = firestore.SERVER_TIMESTAMP
            doc_dict["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.documents_collection.document(str(document.id)).set(doc_dict)
            
            logger.info(
                "Document created successfully",
                document_id=str(document.id),
                filename=document.filename
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to create document",
                document_id=str(document.id),
                error=str(e)
            )
            raise
    
    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        try:
            doc = await self.documents_collection.document(str(document_id)).get()
            
            if not doc.exists:
                return None
            
            doc_data = doc.to_dict()
            return Document(**doc_data)
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get document",
                document_id=str(document_id),
                error=str(e)
            )
            raise
    
    async def update_document(self, document: Document) -> None:
        """Update an existing document."""
        try:
            doc_dict = document.model_dump(mode="json", exclude={"id", "created_at"})
            doc_dict["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.documents_collection.document(str(document.id)).update(doc_dict)
            
            logger.info(
                "Document updated successfully",
                document_id=str(document.id)
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to update document",
                document_id=str(document.id),
                error=str(e)
            )
            raise
    
    async def get_document_raw(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get raw document data by ID."""
        try:
            doc = await self.documents_collection.document(document_id).get()
            
            if not doc.exists:
                return None
            
            return doc.to_dict()
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get raw document",
                document_id=document_id,
                error=str(e)
            )
            raise
    
    async def update_document_fields(self, document_id: str, fields: Dict[str, Any]) -> None:
        """Update specific fields of a document."""
        try:
            fields["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.documents_collection.document(document_id).update(fields)
            
            logger.info(
                "Document fields updated successfully",
                document_id=document_id,
                fields=list(fields.keys())
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to update document fields",
                document_id=document_id,
                error=str(e)
            )
            raise
    
    async def get_user_documents(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """Get documents for a specific user."""
        try:
            query = (
                self.documents_collection
                .where("user_id", "==", user_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )
            
            docs = await query.stream()
            documents = []
            
            async for doc in docs:
                doc_data = doc.to_dict()
                documents.append(Document(**doc_data))
            
            logger.info(
                "Retrieved user documents",
                user_id=user_id,
                count=len(documents)
            )
            
            return documents
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get user documents",
                user_id=user_id,
                error=str(e)
            )
            raise
    
    # Job operations
    async def create_job(self, job: Job) -> None:
        """Create a new job record."""
        try:
            job_dict = job.model_dump(mode="json")
            job_dict["created_at"] = firestore.SERVER_TIMESTAMP
            job_dict["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.jobs_collection.document(str(job.id)).set(job_dict)
            
            logger.info(
                "Job created successfully",
                job_id=str(job.id),
                document_id=str(job.document_id)
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to create job",
                job_id=str(job.id),
                error=str(e)
            )
            raise
    
    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get a job by ID."""
        try:
            doc = await self.jobs_collection.document(str(job_id)).get()
            
            if not doc.exists:
                return None
            
            job_data = doc.to_dict()
            return Job(**job_data)
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get job",
                job_id=str(job_id),
                error=str(e)
            )
            raise
    
    async def update_job(self, job: Job) -> None:
        """Update an existing job."""
        try:
            job_dict = job.model_dump(mode="json", exclude={"id", "created_at"})
            job_dict["updated_at"] = firestore.SERVER_TIMESTAMP
            
            await self.jobs_collection.document(str(job.id)).update(job_dict)
            
            logger.info("Job updated successfully", job_id=str(job.id))
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to update job",
                job_id=str(job.id),
                error=str(e)
            )
            raise
    
    async def update_job_progress(
        self,
        job_id: UUID,
        progress: JobProgress
    ) -> None:
        """Update job progress."""
        try:
            progress_dict = progress.model_dump(mode="json")
            
            # Update job with new progress
            await self.jobs_collection.document(str(job_id)).update({
                "current_stage": progress.stage.value,
                "progress_percentage": progress.percentage,
                "progress": firestore.ArrayUnion([progress_dict]),
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            logger.info(
                "Job progress updated",
                job_id=str(job_id),
                stage=progress.stage.value,
                percentage=progress.percentage
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to update job progress",
                job_id=str(job_id),
                error=str(e)
            )
            raise
    
    async def get_user_jobs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """Get jobs for a specific user."""
        try:
            query = (
                self.jobs_collection
                .where("user_id", "==", user_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )
            
            docs = await query.stream()
            jobs = []
            
            async for doc in docs:
                job_data = doc.to_dict()
                jobs.append(Job(**job_data))
            
            logger.info(
                "Retrieved user jobs",
                user_id=user_id,
                count=len(jobs)
            )
            
            return jobs
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get user jobs",
                user_id=user_id,
                error=str(e)
            )
            raise
    
    # Clause operations
    async def create_clauses(self, clauses: List[Clause]) -> None:
        """Create multiple clause records in batch."""
        try:
            batch = self.client.batch()
            
            for clause in clauses:
                clause_dict = clause.model_dump(mode="json")
                clause_dict["created_at"] = firestore.SERVER_TIMESTAMP
                clause_dict["updated_at"] = firestore.SERVER_TIMESTAMP
                
                doc_ref = self.clauses_collection.document(str(clause.id))
                batch.set(doc_ref, clause_dict)
            
            await batch.commit()
            
            logger.info(
                "Clauses created successfully",
                count=len(clauses),
                document_id=str(clauses[0].document_id) if clauses else None
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to create clauses",
                count=len(clauses),
                error=str(e)
            )
            raise
    
    async def get_document_clauses(self, document_id: UUID) -> List[Clause]:
        """Get all clauses for a document."""
        try:
            query = (
                self.clauses_collection
                .where("document_id", "==", str(document_id))
                .order_by("created_at")
            )
            
            docs = await query.stream()
            clauses = []
            
            async for doc in docs:
                clause_data = doc.to_dict()
                clauses.append(Clause(**clause_data))
            
            logger.info(
                "Retrieved document clauses",
                document_id=str(document_id),
                count=len(clauses)
            )
            
            return clauses
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get document clauses",
                document_id=str(document_id),
                error=str(e)
            )
            raise
    
    # Results operations
    async def create_job_results(self, results: JobResults) -> None:
        """Create job results record."""
        try:
            results_dict = results.model_dump(mode="json")
            results_dict["created_at"] = firestore.SERVER_TIMESTAMP
            
            await self.results_collection.document(str(results.job_id)).set(results_dict)
            
            logger.info(
                "Job results created successfully",
                job_id=str(results.job_id)
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to create job results",
                job_id=str(results.job_id),
                error=str(e)
            )
            raise
    
    async def get_job_results(self, job_id: UUID) -> Optional[JobResults]:
        """Get job results by job ID."""
        try:
            doc = await self.results_collection.document(str(job_id)).get()
            
            if not doc.exists:
                return None
            
            results_data = doc.to_dict()
            return JobResults(**results_data)
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to get job results",
                job_id=str(job_id),
                error=str(e)
            )
            raise
    
    # Real-time listeners
    def listen_to_job_updates(
        self,
        job_id: UUID,
        callback: callable
    ) -> firestore.Watch:
        """
        Set up real-time listener for job updates.
        
        Args:
            job_id: Job ID to listen to
            callback: Function to call when job is updated
            
        Returns:
            Firestore watch object
        """
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                if change.type.name in ['ADDED', 'MODIFIED']:
                    job_data = change.document.to_dict()
                    job = Job(**job_data)
                    callback(job)
        
        doc_ref = self.jobs_collection.document(str(job_id))
        return doc_ref.on_snapshot(on_snapshot)
    
    # Utility methods
    async def delete_user_data(self, user_id: str) -> None:
        """
        Delete all data for a user (GDPR compliance).
        
        Args:
            user_id: User ID to delete data for
        """
        try:
            batch = self.client.batch()
            
            # Delete user documents
            docs_query = self.documents_collection.where("user_id", "==", user_id)
            docs = await docs_query.stream()
            
            document_ids = []
            async for doc in docs:
                document_ids.append(doc.id)
                batch.delete(doc.reference)
            
            # Delete user jobs
            jobs_query = self.jobs_collection.where("user_id", "==", user_id)
            jobs = await jobs_query.stream()
            
            job_ids = []
            async for job in jobs:
                job_ids.append(job.id)
                batch.delete(job.reference)
            
            # Delete clauses for user documents
            for doc_id in document_ids:
                clauses_query = self.clauses_collection.where("document_id", "==", doc_id)
                clauses = await clauses_query.stream()
                
                async for clause in clauses:
                    batch.delete(clause.reference)
            
            # Delete job results
            for job_id in job_ids:
                results_ref = self.results_collection.document(job_id)
                batch.delete(results_ref)
            
            # Delete user record
            user_ref = self.users_collection.document(user_id)
            batch.delete(user_ref)
            
            await batch.commit()
            
            logger.info(
                "User data deleted successfully",
                user_id=user_id,
                documents_count=len(document_ids),
                jobs_count=len(job_ids)
            )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to delete user data",
                user_id=user_id,
                error=str(e)
            )
            raise
    
    async def cleanup_expired_data(self, days: int = 30) -> None:
        """
        Clean up data older than specified days.
        
        Args:
            days: Number of days to keep data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Find expired documents
            docs_query = (
                self.documents_collection
                .where("created_at", "<", cutoff_date)
                .limit(100)  # Process in batches
            )
            
            docs = await docs_query.stream()
            expired_doc_ids = []
            
            async for doc in docs:
                expired_doc_ids.append(doc.id)
            
            if expired_doc_ids:
                # Delete in batches
                batch = self.client.batch()
                
                for doc_id in expired_doc_ids:
                    # Delete document
                    doc_ref = self.documents_collection.document(doc_id)
                    batch.delete(doc_ref)
                    
                    # Delete associated clauses
                    clauses_query = self.clauses_collection.where("document_id", "==", doc_id)
                    clauses = await clauses_query.stream()
                    
                    async for clause in clauses:
                        batch.delete(clause.reference)
                
                await batch.commit()
                
                logger.info(
                    "Expired data cleaned up",
                    documents_deleted=len(expired_doc_ids),
                    cutoff_date=cutoff_date
                )
            
        except GoogleCloudError as e:
            logger.error(
                "Failed to cleanup expired data",
                error=str(e)
            )
            raise