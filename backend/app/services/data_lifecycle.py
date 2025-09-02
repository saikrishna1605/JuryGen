"""
Data Lifecycle and Retention Management Service.

This service handles:
- Automatic data deletion with configurable retention periods
- User consent management for data usage
- Data residency controls and regional storage options
- Compliance with data protection regulations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from google.cloud import storage
from google.cloud import firestore
from google.cloud import scheduler_v1
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..core.exceptions import DatabaseError, StorageError, ConfigurationError
from ..services.firestore import FirestoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class DataCategory(str, Enum):
    """Categories of data for retention policies."""
    DOCUMENTS = "documents"
    ANALYSIS_RESULTS = "analysis_results"
    AUDIO_FILES = "audio_files"
    EXPORTS = "exports"
    USER_PREFERENCES = "user_preferences"
    AUDIT_LOGS = "audit_logs"
    PII_LOGS = "pii_logs"
    TEMPORARY_FILES = "temporary_files"


class RetentionPeriod(str, Enum):
    """Standard retention periods."""
    IMMEDIATE = "immediate"  # Delete immediately after use
    DAYS_7 = "7_days"
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_180 = "180_days"
    YEAR_1 = "1_year"
    YEARS_3 = "3_years"
    YEARS_7 = "7_years"
    PERMANENT = "permanent"


class DataResidency(str, Enum):
    """Data residency regions."""
    US = "us"
    EU = "eu"
    ASIA = "asia"
    GLOBAL = "global"


class ConsentType(str, Enum):
    """Types of user consent."""
    DATA_PROCESSING = "data_processing"
    MODEL_TRAINING = "model_training"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"


class DataLifecycleService:
    """
    Service for managing data lifecycle and retention policies.
    
    Handles automatic deletion, user consent, and data residency controls.
    """
    
    def __init__(self):
        """Initialize the data lifecycle service."""
        # Initialize clients
        self.storage_client = storage.Client()
        self.firestore_service = FirestoreService()
        self.scheduler_client = scheduler_v1.CloudSchedulerClient()
        
        # Project configuration
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.VERTEX_AI_LOCATION
        
        # Default retention policies
        self.default_retention_policies = {
            DataCategory.DOCUMENTS: RetentionPeriod.DAYS_30,
            DataCategory.ANALYSIS_RESULTS: RetentionPeriod.DAYS_90,
            DataCategory.AUDIO_FILES: RetentionPeriod.DAYS_7,
            DataCategory.EXPORTS: RetentionPeriod.DAYS_30,
            DataCategory.USER_PREFERENCES: RetentionPeriod.PERMANENT,
            DataCategory.AUDIT_LOGS: RetentionPeriod.YEARS_7,
            DataCategory.PII_LOGS: RetentionPeriod.YEARS_3,
            DataCategory.TEMPORARY_FILES: RetentionPeriod.IMMEDIATE
        }
        
        # Regional storage buckets
        self.regional_buckets = {
            DataResidency.US: f"{settings.STORAGE_BUCKET}-us",
            DataResidency.EU: f"{settings.STORAGE_BUCKET}-eu",
            DataResidency.ASIA: f"{settings.STORAGE_BUCKET}-asia",
            DataResidency.GLOBAL: settings.STORAGE_BUCKET
        }
    
    async def create_retention_policy(
        self,
        user_id: str,
        data_category: DataCategory,
        retention_period: RetentionPeriod,
        custom_days: Optional[int] = None
    ) -> str:
        """
        Create or update a retention policy for a user and data category.
        
        Args:
            user_id: User identifier
            data_category: Category of data
            retention_period: Standard retention period
            custom_days: Custom retention period in days (overrides standard)
            
        Returns:
            Policy ID
        """
        try:
            # Calculate expiration date
            if custom_days:
                expiration_date = datetime.utcnow() + timedelta(days=custom_days)
                retention_days = custom_days
            else:
                retention_days = self._get_retention_days(retention_period)
                if retention_days == -1:  # Permanent
                    expiration_date = None
                else:
                    expiration_date = datetime.utcnow() + timedelta(days=retention_days)
            
            # Create policy document
            policy_data = {
                "user_id": user_id,
                "data_category": data_category,
                "retention_period": retention_period,
                "retention_days": retention_days,
                "expiration_date": expiration_date,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            # Store in Firestore
            policy_id = await self.firestore_service.create_document(
                collection="retention_policies",
                data=policy_data
            )
            
            # Schedule cleanup job if not permanent
            if expiration_date:
                await self._schedule_cleanup_job(policy_id, expiration_date)
            
            logger.info(f"Created retention policy {policy_id} for user {user_id}")
            return policy_id
            
        except Exception as e:
            logger.error(f"Error creating retention policy: {e}")
            raise DatabaseError(f"Failed to create retention policy: {e}")
    
    async def apply_retention_to_document(
        self,
        document_id: str,
        user_id: str,
        data_category: DataCategory = DataCategory.DOCUMENTS
    ) -> None:
        """
        Apply retention policy to a specific document.
        
        Args:
            document_id: Document identifier
            user_id: User identifier
            data_category: Category of data
        """
        try:
            # Get user's retention policy for this category
            policy = await self._get_user_retention_policy(user_id, data_category)
            
            if not policy:
                # Use default policy
                retention_period = self.default_retention_policies[data_category]
                retention_days = self._get_retention_days(retention_period)
            else:
                retention_days = policy["retention_days"]
            
            # Calculate expiration date
            if retention_days == -1:  # Permanent
                expiration_date = None
            else:
                expiration_date = datetime.utcnow() + timedelta(days=retention_days)
            
            # Update document with retention info
            await self.firestore_service.update_document(
                collection="documents",
                document_id=document_id,
                data={
                    "retention_policy": {
                        "data_category": data_category,
                        "retention_days": retention_days,
                        "expiration_date": expiration_date,
                        "applied_at": datetime.utcnow()
                    }
                }
            )
            
            # Schedule deletion if not permanent
            if expiration_date:
                await self._schedule_document_deletion(document_id, expiration_date)
            
            logger.info(f"Applied retention policy to document {document_id}")
            
        except Exception as e:
            logger.error(f"Error applying retention policy: {e}")
            raise DatabaseError(f"Failed to apply retention policy: {e}")
    
    async def delete_expired_data(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Delete expired data based on retention policies.
        
        Args:
            batch_size: Number of items to process in each batch
            
        Returns:
            Dictionary with deletion counts by category
        """
        deletion_counts = {category.value: 0 for category in DataCategory}
        
        try:
            # Find expired documents
            expired_documents = await self._find_expired_documents(batch_size)
            
            for doc in expired_documents:
                try:
                    await self._delete_document_and_assets(doc)
                    category = doc.get("retention_policy", {}).get("data_category", "unknown")
                    if category in deletion_counts:
                        deletion_counts[category] += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting document {doc.get('id')}: {e}")
            
            # Find expired audit logs
            expired_logs = await self._find_expired_audit_logs(batch_size)
            
            for log in expired_logs:
                try:
                    await self.firestore_service.delete_document(
                        collection="audit_logs",
                        document_id=log["id"]
                    )
                    deletion_counts[DataCategory.AUDIT_LOGS] += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting audit log {log.get('id')}: {e}")
            
            # Find expired PII logs
            expired_pii_logs = await self._find_expired_pii_logs(batch_size)
            
            for log in expired_pii_logs:
                try:
                    await self.firestore_service.delete_document(
                        collection="pii_audit_logs",
                        document_id=log["id"]
                    )
                    deletion_counts[DataCategory.PII_LOGS] += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting PII log {log.get('id')}: {e}")
            
            logger.info(f"Deleted expired data: {deletion_counts}")
            return deletion_counts
            
        except Exception as e:
            logger.error(f"Error in batch deletion: {e}")
            raise DatabaseError(f"Failed to delete expired data: {e}")
    
    async def manage_user_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record user consent for data usage.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent is granted
            metadata: Additional consent metadata
            
        Returns:
            Consent record ID
        """
        try:
            consent_data = {
                "user_id": user_id,
                "consent_type": consent_type,
                "granted": granted,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {},
                "ip_address": metadata.get("ip_address") if metadata else None,
                "user_agent": metadata.get("user_agent") if metadata else None
            }
            
            # Store consent record
            consent_id = await self.firestore_service.create_document(
                collection="user_consents",
                data=consent_data
            )
            
            # Update user profile with current consent status
            await self.firestore_service.update_document(
                collection="users",
                document_id=user_id,
                data={
                    f"consents.{consent_type}": {
                        "granted": granted,
                        "timestamp": datetime.utcnow(),
                        "consent_id": consent_id
                    }
                }
            )
            
            logger.info(f"Recorded consent {consent_type} for user {user_id}: {granted}")
            return consent_id
            
        except Exception as e:
            logger.error(f"Error managing user consent: {e}")
            raise DatabaseError(f"Failed to manage user consent: {e}")
    
    async def check_user_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has granted specific consent.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to check
            
        Returns:
            True if consent is granted, False otherwise
        """
        try:
            user_doc = await self.firestore_service.get_document(
                collection="users",
                document_id=user_id
            )
            
            if not user_doc:
                return False
            
            consents = user_doc.get("consents", {})
            consent_info = consents.get(consent_type, {})
            
            return consent_info.get("granted", False)
            
        except Exception as e:
            logger.error(f"Error checking user consent: {e}")
            return False
    
    async def set_data_residency(
        self,
        user_id: str,
        residency: DataResidency
    ) -> None:
        """
        Set data residency preference for a user.
        
        Args:
            user_id: User identifier
            residency: Preferred data residency region
        """
        try:
            # Update user profile
            await self.firestore_service.update_document(
                collection="users",
                document_id=user_id,
                data={
                    "data_residency": residency,
                    "updated_at": datetime.utcnow()
                }
            )
            
            # TODO: Migrate existing data to appropriate region if needed
            # This would be a complex operation requiring careful planning
            
            logger.info(f"Set data residency for user {user_id}: {residency}")
            
        except Exception as e:
            logger.error(f"Error setting data residency: {e}")
            raise DatabaseError(f"Failed to set data residency: {e}")
    
    async def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary of user's data and retention policies.
        
        Args:
            user_id: User identifier
            
        Returns:
            Data summary including retention policies and consent status
        """
        try:
            # Get user profile
            user_doc = await self.firestore_service.get_document(
                collection="users",
                document_id=user_id
            )
            
            # Get user's documents
            documents = await self.firestore_service.query_documents(
                collection="documents",
                filters=[("user_id", "==", user_id)]
            )
            
            # Get retention policies
            policies = await self.firestore_service.query_documents(
                collection="retention_policies",
                filters=[("user_id", "==", user_id), ("is_active", "==", True)]
            )
            
            # Calculate storage usage by category
            storage_usage = {}
            for doc in documents:
                category = doc.get("retention_policy", {}).get("data_category", "unknown")
                size = doc.get("size_bytes", 0)
                storage_usage[category] = storage_usage.get(category, 0) + size
            
            # Get consent status
            consents = user_doc.get("consents", {}) if user_doc else {}
            
            summary = {
                "user_id": user_id,
                "data_residency": user_doc.get("data_residency", DataResidency.GLOBAL) if user_doc else DataResidency.GLOBAL,
                "total_documents": len(documents),
                "storage_usage_bytes": sum(storage_usage.values()),
                "storage_by_category": storage_usage,
                "retention_policies": {
                    policy["data_category"]: {
                        "retention_period": policy["retention_period"],
                        "retention_days": policy["retention_days"],
                        "expiration_date": policy["expiration_date"].isoformat() if policy["expiration_date"] else None
                    }
                    for policy in policies
                },
                "consents": {
                    consent_type: {
                        "granted": consent_info["granted"],
                        "timestamp": consent_info["timestamp"].isoformat()
                    }
                    for consent_type, consent_info in consents.items()
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting user data summary: {e}")
            raise DatabaseError(f"Failed to get user data summary: {e}")
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data for GDPR compliance.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete user data export
        """
        try:
            # Get all user data
            user_profile = await self.firestore_service.get_document(
                collection="users",
                document_id=user_id
            )
            
            documents = await self.firestore_service.query_documents(
                collection="documents",
                filters=[("user_id", "==", user_id)]
            )
            
            jobs = await self.firestore_service.query_documents(
                collection="jobs",
                filters=[("user_id", "==", user_id)]
            )
            
            consents = await self.firestore_service.query_documents(
                collection="user_consents",
                filters=[("user_id", "==", user_id)]
            )
            
            audit_logs = await self.firestore_service.query_documents(
                collection="audit_logs",
                filters=[("user_id", "==", user_id)]
            )
            
            # Compile export
            export_data = {
                "user_profile": user_profile,
                "documents": documents,
                "jobs": jobs,
                "consents": consents,
                "audit_logs": audit_logs,
                "export_timestamp": datetime.utcnow().isoformat(),
                "export_version": "1.0"
            }
            
            # Log the export
            await self.firestore_service.create_document(
                collection="data_exports",
                data={
                    "user_id": user_id,
                    "export_timestamp": datetime.utcnow(),
                    "data_categories": list(export_data.keys()),
                    "total_records": sum(len(v) if isinstance(v, list) else 1 for v in export_data.values())
                }
            )
            
            logger.info(f"Exported user data for {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            raise DatabaseError(f"Failed to export user data: {e}")
    
    async def delete_user_data(self, user_id: str) -> Dict[str, int]:
        """
        Delete all user data (right to be forgotten).
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with deletion counts by category
        """
        deletion_counts = {}
        
        try:
            # Delete documents and associated files
            documents = await self.firestore_service.query_documents(
                collection="documents",
                filters=[("user_id", "==", user_id)]
            )
            
            for doc in documents:
                await self._delete_document_and_assets(doc)
            deletion_counts["documents"] = len(documents)
            
            # Delete jobs
            jobs = await self.firestore_service.query_documents(
                collection="jobs",
                filters=[("user_id", "==", user_id)]
            )
            
            for job in jobs:
                await self.firestore_service.delete_document(
                    collection="jobs",
                    document_id=job["id"]
                )
            deletion_counts["jobs"] = len(jobs)
            
            # Delete consents
            consents = await self.firestore_service.query_documents(
                collection="user_consents",
                filters=[("user_id", "==", user_id)]
            )
            
            for consent in consents:
                await self.firestore_service.delete_document(
                    collection="user_consents",
                    document_id=consent["id"]
                )
            deletion_counts["consents"] = len(consents)
            
            # Delete retention policies
            policies = await self.firestore_service.query_documents(
                collection="retention_policies",
                filters=[("user_id", "==", user_id)]
            )
            
            for policy in policies:
                await self.firestore_service.delete_document(
                    collection="retention_policies",
                    document_id=policy["id"]
                )
            deletion_counts["policies"] = len(policies)
            
            # Anonymize audit logs (don't delete for compliance)
            audit_logs = await self.firestore_service.query_documents(
                collection="audit_logs",
                filters=[("user_id", "==", user_id)]
            )
            
            for log in audit_logs:
                await self.firestore_service.update_document(
                    collection="audit_logs",
                    document_id=log["id"],
                    data={
                        "user_id": "[DELETED]",
                        "anonymized_at": datetime.utcnow()
                    }
                )
            deletion_counts["anonymized_logs"] = len(audit_logs)
            
            # Delete user profile (last)
            await self.firestore_service.delete_document(
                collection="users",
                document_id=user_id
            )
            deletion_counts["user_profile"] = 1
            
            # Log the deletion
            await self.firestore_service.create_document(
                collection="data_deletions",
                data={
                    "user_id": user_id,
                    "deletion_timestamp": datetime.utcnow(),
                    "deletion_counts": deletion_counts,
                    "total_items_deleted": sum(deletion_counts.values())
                }
            )
            
            logger.info(f"Deleted all data for user {user_id}: {deletion_counts}")
            return deletion_counts
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            raise DatabaseError(f"Failed to delete user data: {e}")
    
    def _get_retention_days(self, retention_period: RetentionPeriod) -> int:
        """Convert retention period to days."""
        mapping = {
            RetentionPeriod.IMMEDIATE: 0,
            RetentionPeriod.DAYS_7: 7,
            RetentionPeriod.DAYS_30: 30,
            RetentionPeriod.DAYS_90: 90,
            RetentionPeriod.DAYS_180: 180,
            RetentionPeriod.YEAR_1: 365,
            RetentionPeriod.YEARS_3: 1095,
            RetentionPeriod.YEARS_7: 2555,
            RetentionPeriod.PERMANENT: -1
        }
        return mapping.get(retention_period, 30)
    
    async def _get_user_retention_policy(
        self,
        user_id: str,
        data_category: DataCategory
    ) -> Optional[Dict[str, Any]]:
        """Get user's retention policy for a data category."""
        policies = await self.firestore_service.query_documents(
            collection="retention_policies",
            filters=[
                ("user_id", "==", user_id),
                ("data_category", "==", data_category),
                ("is_active", "==", True)
            ]
        )
        return policies[0] if policies else None
    
    async def _schedule_cleanup_job(self, policy_id: str, expiration_date: datetime) -> None:
        """Schedule a cleanup job for expired data."""
        # This would integrate with Cloud Scheduler or similar
        # For now, we'll just log the scheduling
        logger.info(f"Scheduled cleanup for policy {policy_id} at {expiration_date}")
    
    async def _schedule_document_deletion(self, document_id: str, expiration_date: datetime) -> None:
        """Schedule document deletion."""
        # This would integrate with Cloud Scheduler or similar
        # For now, we'll just log the scheduling
        logger.info(f"Scheduled deletion for document {document_id} at {expiration_date}")
    
    async def _find_expired_documents(self, limit: int) -> List[Dict[str, Any]]:
        """Find documents that have expired."""
        return await self.firestore_service.query_documents(
            collection="documents",
            filters=[("retention_policy.expiration_date", "<=", datetime.utcnow())],
            limit=limit
        )
    
    async def _find_expired_audit_logs(self, limit: int) -> List[Dict[str, Any]]:
        """Find expired audit logs."""
        # Audit logs expire after 7 years by default
        expiration_date = datetime.utcnow() - timedelta(days=2555)
        return await self.firestore_service.query_documents(
            collection="audit_logs",
            filters=[("timestamp", "<=", expiration_date)],
            limit=limit
        )
    
    async def _find_expired_pii_logs(self, limit: int) -> List[Dict[str, Any]]:
        """Find expired PII audit logs."""
        # PII logs expire after 3 years by default
        expiration_date = datetime.utcnow() - timedelta(days=1095)
        return await self.firestore_service.query_documents(
            collection="pii_audit_logs",
            filters=[("timestamp", "<=", expiration_date)],
            limit=limit
        )
    
    async def _delete_document_and_assets(self, document: Dict[str, Any]) -> None:
        """Delete document and all associated assets."""
        document_id = document["id"]
        
        try:
            # Delete from Cloud Storage
            if "storage_url" in document:
                blob_name = document["storage_url"].split("/")[-1]
                bucket = self.storage_client.bucket(settings.STORAGE_BUCKET)
                blob = bucket.blob(blob_name)
                if blob.exists():
                    blob.delete()
            
            # Delete analysis results
            await self.firestore_service.delete_documents_by_query(
                collection="clauses",
                filters=[("document_id", "==", document_id)]
            )
            
            # Delete exports
            await self.firestore_service.delete_documents_by_query(
                collection="exports",
                filters=[("document_id", "==", document_id)]
            )
            
            # Delete the document record
            await self.firestore_service.delete_document(
                collection="documents",
                document_id=document_id
            )
            
            logger.info(f"Deleted document {document_id} and all assets")
            
        except Exception as e:
            logger.error(f"Error deleting document assets: {e}")
            raise StorageError(f"Failed to delete document assets: {e}")


# Singleton instance
data_lifecycle_service = DataLifecycleService()