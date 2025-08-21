"""
Job Management System for tracking and managing document processing jobs.

This service handles:
- Job creation, queuing, and status tracking in Firestore
- Job progress calculation and ETA estimation
- Job cancellation and cleanup functionality
- Real-time status updates and notifications
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

from google.cloud import firestore
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..models.base import ProcessingStatus, ProcessingStage
from ..models.document import Document
from ..core.exceptions import WorkflowError
from .firestore import FirestoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class JobResult:
    """Represents the result of a completed job."""
    
    def __init__(
        self,
        job_id: str,
        status: ProcessingStatus,
        results: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.job_id = job_id
        self.status = status
        self.results = results or {}
        self.error = error
        self.completed_at = datetime.utcnow()


class Job:
    """Represents a document processing job."""
    
    def __init__(
        self,
        job_id: str,
        document_id: str,
        user_id: str,
        job_type: str = "document_analysis",
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.job_id = job_id
        self.document_id = document_id
        self.user_id = user_id
        self.job_type = job_type
        self.priority = priority
        self.metadata = metadata or {}
        
        # Status tracking
        self.status = ProcessingStatus.QUEUED
        self.current_stage = ProcessingStage.UPLOAD
        self.progress_percentage = 0
        self.error_message = None
        
        # Timing
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.estimated_completion = None
        
        # Results
        self.results = {}
        
        # Retry tracking
        self.retry_count = 0
        self.max_retries = 3
        
        # Progress callbacks
        self.progress_callbacks = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for storage."""
        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "job_type": self.job_type,
            "priority": self.priority,
            "metadata": self.metadata,
            "status": self.status.value,
            "current_stage": self.current_stage.value,
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "estimated_completion": self.estimated_completion,
            "results": self.results,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create job from dictionary."""
        job = cls(
            job_id=data["job_id"],
            document_id=data["document_id"],
            user_id=data["user_id"],
            job_type=data.get("job_type", "document_analysis"),
            priority=data.get("priority", 1),
            metadata=data.get("metadata", {})
        )
        
        # Restore status
        job.status = ProcessingStatus(data.get("status", ProcessingStatus.QUEUED))
        job.current_stage = ProcessingStage(data.get("current_stage", ProcessingStage.UPLOAD))
        job.progress_percentage = data.get("progress_percentage", 0)
        job.error_message = data.get("error_message")
        
        # Restore timing
        job.created_at = data.get("created_at", datetime.utcnow())
        job.started_at = data.get("started_at")
        job.completed_at = data.get("completed_at")
        job.estimated_completion = data.get("estimated_completion")
        
        # Restore results and retry info
        job.results = data.get("results", {})
        job.retry_count = data.get("retry_count", 0)
        job.max_retries = data.get("max_retries", 3)
        
        return job


class JobManager:
    """
    Manages document processing jobs with real-time status tracking.
    
    Provides job queuing, progress tracking, ETA estimation, and
    cancellation capabilities with Firestore persistence.
    """
    
    def __init__(self):
        """Initialize the Job Manager."""
        self.firestore_service = FirestoreService()
        
        # Job queues by priority
        self.job_queues = {
            1: [],  # Low priority
            2: [],  # Normal priority  
            3: [],  # High priority
            4: []   # Critical priority
        }
        
        # Active jobs
        self.active_jobs = {}
        
        # Job statistics for ETA calculation
        self.job_stats = {
            "average_processing_times": {},  # By stage
            "completion_rates": {},          # By job type
            "recent_jobs": []               # For trend analysis
        }
        
        # Progress callbacks
        self.global_progress_callbacks = []
        
        # Background task for job processing
        self._processing_task = None
        self._shutdown_event = asyncio.Event()
    
    async def create_job(
        self,
        document_id: str,
        user_id: str,
        job_type: str = "document_analysis",
        priority: int = 2,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new processing job.
        
        Args:
            document_id: ID of the document to process
            user_id: ID of the user requesting processing
            job_type: Type of processing job
            priority: Job priority (1-4, higher is more urgent)
            metadata: Additional job metadata
            
        Returns:
            Job ID
            
        Raises:
            WorkflowError: If job creation fails
        """
        try:
            job_id = str(uuid4())
            
            # Create job object
            job = Job(
                job_id=job_id,
                document_id=document_id,
                user_id=user_id,
                job_type=job_type,
                priority=priority,
                metadata=metadata
            )
            
            # Store job in Firestore
            await self.firestore_service.create_document(
                "jobs",
                job_id,
                job.to_dict()
            )
            
            # Add to appropriate queue
            self.job_queues[priority].append(job)
            
            # Sort queue by creation time (FIFO within priority)
            self.job_queues[priority].sort(key=lambda j: j.created_at)
            
            logger.info(f"Created job {job_id} for document {document_id}")
            
            # Start processing if not already running
            if not self._processing_task or self._processing_task.done():
                self._processing_task = asyncio.create_task(self._process_job_queue())
            
            return job_id
            
        except Exception as e:
            logger.error(f"Job creation failed: {str(e)}")
            raise WorkflowError(f"Failed to create job: {str(e)}") from e
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job status information or None if not found
        """
        try:
            # Check active jobs first
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return self._format_job_status(job)
            
            # Check Firestore
            job_data = await self.firestore_service.get_document("jobs", job_id)
            if job_data:
                job = Job.from_dict(job_data)
                return self._format_job_status(job)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job status: {str(e)}")
            return None
    
    def _format_job_status(self, job: Job) -> Dict[str, Any]:
        """Format job status for API response."""
        status = {
            "job_id": job.job_id,
            "document_id": job.document_id,
            "status": job.status.value,
            "current_stage": job.current_stage.value,
            "progress_percentage": job.progress_percentage,
            "created_at": job.created_at.isoformat(),
            "estimated_completion": job.estimated_completion.isoformat() if job.estimated_completion else None
        }
        
        # Add timing information
        if job.started_at:
            status["started_at"] = job.started_at.isoformat()
        if job.completed_at:
            status["completed_at"] = job.completed_at.isoformat()
            
        # Add error information
        if job.error_message:
            status["error_message"] = job.error_message
            
        # Add results if completed
        if job.status == ProcessingStatus.COMPLETED and job.results:
            status["results"] = job.results
            
        return status
    
    async def update_job_progress(
        self,
        job_id: str,
        stage: ProcessingStage,
        progress: int,
        message: Optional[str] = None
    ) -> bool:
        """
        Update job progress and stage.
        
        Args:
            job_id: Job ID to update
            stage: Current processing stage
            progress: Progress percentage (0-100)
            message: Optional progress message
            
        Returns:
            True if update was successful
        """
        try:
            # Find job
            job = None
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            else:
                # Load from Firestore
                job_data = await self.firestore_service.get_document("jobs", job_id)
                if job_data:
                    job = Job.from_dict(job_data)
            
            if not job:
                logger.warning(f"Job {job_id} not found for progress update")
                return False
            
            # Update job status
            job.current_stage = stage
            job.progress_percentage = min(100, max(0, progress))
            
            if job.status == ProcessingStatus.QUEUED:
                job.status = ProcessingStatus.PROCESSING
                job.started_at = datetime.utcnow()
            
            # Update ETA
            job.estimated_completion = self._calculate_eta(job)
            
            # Store updated job
            await self.firestore_service.update_document(
                "jobs",
                job_id,
                job.to_dict()
            )
            
            # Notify progress callbacks
            await self._notify_progress_callbacks(job, message)
            
            logger.debug(f"Updated job {job_id}: {stage.value} - {progress}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job progress: {str(e)}")
            return False
    
    async def complete_job(
        self,
        job_id: str,
        results: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Mark a job as completed.
        
        Args:
            job_id: Job ID to complete
            results: Job results
            success: Whether job completed successfully
            error_message: Error message if failed
            
        Returns:
            True if completion was successful
        """
        try:
            # Find job
            job = None
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            else:
                job_data = await self.firestore_service.get_document("jobs", job_id)
                if job_data:
                    job = Job.from_dict(job_data)
            
            if not job:
                logger.warning(f"Job {job_id} not found for completion")
                return False
            
            # Update job status
            job.status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
            job.progress_percentage = 100 if success else job.progress_percentage
            job.completed_at = datetime.utcnow()
            job.results = results
            job.error_message = error_message
            
            # Store completed job
            await self.firestore_service.update_document(
                "jobs",
                job_id,
                job.to_dict()
            )
            
            # Remove from active jobs
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            # Update statistics
            await self._update_job_statistics(job)
            
            # Notify completion
            await self._notify_progress_callbacks(job, "Job completed")
            
            logger.info(f"Completed job {job_id}: {'success' if success else 'failed'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete job: {str(e)}")
            return False
    
    async def cancel_job(self, job_id: str, reason: str = "User cancelled") -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID to cancel
            reason: Cancellation reason
            
        Returns:
            True if cancellation was successful
        """
        try:
            # Find job
            job = None
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            else:
                job_data = await self.firestore_service.get_document("jobs", job_id)
                if job_data:
                    job = Job.from_dict(job_data)
            
            if not job:
                logger.warning(f"Job {job_id} not found for cancellation")
                return False
            
            # Can only cancel queued or processing jobs
            if job.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
                logger.warning(f"Cannot cancel job {job_id} in status {job.status}")
                return False
            
            # Update job status
            job.status = ProcessingStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.error_message = reason
            
            # Store cancelled job
            await self.firestore_service.update_document(
                "jobs",
                job_id,
                job.to_dict()
            )
            
            # Remove from queues and active jobs
            for priority_queue in self.job_queues.values():
                priority_queue[:] = [j for j in priority_queue if j.job_id != job_id]
            
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            # Notify cancellation
            await self._notify_progress_callbacks(job, f"Job cancelled: {reason}")
            
            logger.info(f"Cancelled job {job_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job: {str(e)}")
            return False
    
    async def get_user_jobs(
        self,
        user_id: str,
        status_filter: Optional[ProcessingStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get jobs for a specific user.
        
        Args:
            user_id: User ID to filter by
            status_filter: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of job status information
        """
        try:
            # Query Firestore for user jobs
            query = self.firestore_service.db.collection("jobs").where("user_id", "==", user_id)
            
            if status_filter:
                query = query.where("status", "==", status_filter.value)
            
            query = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            
            jobs = []
            for doc in docs:
                job_data = doc.to_dict()
                job = Job.from_dict(job_data)
                jobs.append(self._format_job_status(job))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get user jobs: {str(e)}")
            return []
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status and statistics.
        
        Returns:
            Queue status information
        """
        try:
            queue_status = {
                "queues": {},
                "active_jobs": len(self.active_jobs),
                "total_queued": 0,
                "processing_enabled": not self._shutdown_event.is_set()
            }
            
            # Count jobs in each priority queue
            for priority, queue in self.job_queues.items():
                queue_status["queues"][f"priority_{priority}"] = len(queue)
                queue_status["total_queued"] += len(queue)
            
            # Add recent statistics
            if self.job_stats["recent_jobs"]:
                recent_jobs = self.job_stats["recent_jobs"][-10:]  # Last 10 jobs
                avg_processing_time = sum(
                    (job["completed_at"] - job["started_at"]).total_seconds()
                    for job in recent_jobs
                    if job.get("completed_at") and job.get("started_at")
                ) / len(recent_jobs) if recent_jobs else 0
                
                queue_status["average_processing_time"] = avg_processing_time
                queue_status["recent_completion_rate"] = len([
                    j for j in recent_jobs if j.get("status") == ProcessingStatus.COMPLETED.value
                ]) / len(recent_jobs) if recent_jobs else 0
            
            return queue_status
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_eta(self, job: Job) -> Optional[datetime]:
        """Calculate estimated completion time for a job."""
        try:
            if job.status == ProcessingStatus.COMPLETED:
                return job.completed_at
            
            # Get average processing time for this stage
            stage_times = self.job_stats["average_processing_times"].get(job.current_stage.value)
            if not stage_times:
                return None
            
            # Estimate remaining time based on current progress
            if job.progress_percentage > 0:
                elapsed = (datetime.utcnow() - job.started_at).total_seconds() if job.started_at else 0
                estimated_total = elapsed * (100 / job.progress_percentage)
                remaining = max(0, estimated_total - elapsed)
                
                return datetime.utcnow() + timedelta(seconds=remaining)
            
            return None
            
        except Exception as e:
            logger.warning(f"ETA calculation failed: {str(e)}")
            return None
    
    async def _update_job_statistics(self, job: Job):
        """Update job statistics for ETA calculation."""
        try:
            # Add to recent jobs
            job_stat = {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "status": job.status.value,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "processing_time": (job.completed_at - job.started_at).total_seconds() if job.started_at and job.completed_at else None
            }
            
            self.job_stats["recent_jobs"].append(job_stat)
            
            # Keep only last 100 jobs
            if len(self.job_stats["recent_jobs"]) > 100:
                self.job_stats["recent_jobs"] = self.job_stats["recent_jobs"][-100:]
            
            # Update stage processing times
            if job.started_at and job.completed_at:
                processing_time = (job.completed_at - job.started_at).total_seconds()
                
                if job.current_stage.value not in self.job_stats["average_processing_times"]:
                    self.job_stats["average_processing_times"][job.current_stage.value] = []
                
                stage_times = self.job_stats["average_processing_times"][job.current_stage.value]
                stage_times.append(processing_time)
                
                # Keep only last 50 times per stage
                if len(stage_times) > 50:
                    self.job_stats["average_processing_times"][job.current_stage.value] = stage_times[-50:]
            
        except Exception as e:
            logger.warning(f"Failed to update job statistics: {str(e)}")
    
    async def _notify_progress_callbacks(self, job: Job, message: Optional[str] = None):
        """Notify all progress callbacks about job updates."""
        try:
            # Notify job-specific callbacks
            for callback in job.progress_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(job, message)
                    else:
                        callback(job, message)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {str(e)}")
            
            # Notify global callbacks
            for callback in self.global_progress_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(job, message)
                    else:
                        callback(job, message)
                except Exception as e:
                    logger.warning(f"Global progress callback failed: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to notify progress callbacks: {str(e)}")
    
    def add_progress_callback(self, callback: Callable):
        """Add a global progress callback."""
        self.global_progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable):
        """Remove a global progress callback."""
        if callback in self.global_progress_callbacks:
            self.global_progress_callbacks.remove(callback)
    
    async def _process_job_queue(self):
        """Background task to process jobs from the queue."""
        logger.info("Started job queue processing")
        
        while not self._shutdown_event.is_set():
            try:
                # Get next job from highest priority queue
                next_job = None
                for priority in sorted(self.job_queues.keys(), reverse=True):
                    if self.job_queues[priority]:
                        next_job = self.job_queues[priority].pop(0)
                        break
                
                if next_job:
                    # Move to active jobs
                    self.active_jobs[next_job.job_id] = next_job
                    
                    # Process job (this would trigger the actual workflow)
                    await self._trigger_job_processing(next_job)
                else:
                    # No jobs to process, wait a bit
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Job queue processing error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("Job queue processing stopped")
    
    async def _trigger_job_processing(self, job: Job):
        """Trigger the actual processing of a job."""
        try:
            logger.info(f"Triggering processing for job {job.job_id}")
            
            # This would typically trigger the CrewAI workflow or Cloud Workflows
            # For now, we'll just update the status to indicate processing started
            await self.update_job_progress(
                job.job_id,
                ProcessingStage.OCR,
                5,
                "Starting document processing"
            )
            
            # The actual processing would be handled by the workflow system
            # which would call back to update progress and complete the job
            
        except Exception as e:
            logger.error(f"Failed to trigger job processing: {str(e)}")
            await self.complete_job(
                job.job_id,
                {},
                success=False,
                error_message=f"Failed to start processing: {str(e)}"
            )
    
    async def cleanup_old_jobs(self, days_old: int = 30):
        """Clean up old completed jobs."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Query old completed jobs
            query = (self.firestore_service.db.collection("jobs")
                    .where("status", "in", [ProcessingStatus.COMPLETED.value, ProcessingStatus.FAILED.value, ProcessingStatus.CANCELLED.value])
                    .where("completed_at", "<", cutoff_date))
            
            docs = query.stream()
            
            deleted_count = 0
            for doc in docs:
                await self.firestore_service.delete_document("jobs", doc.id)
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old jobs")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Job cleanup failed: {str(e)}")
            return 0
    
    async def shutdown(self):
        """Shutdown the job manager gracefully."""
        logger.info("Shutting down job manager")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for processing task to complete
        if self._processing_task and not self._processing_task.done():
            try:
                await asyncio.wait_for(self._processing_task, timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Job processing task did not shutdown gracefully")
                self._processing_task.cancel()
        
        logger.info("Job manager shutdown complete")