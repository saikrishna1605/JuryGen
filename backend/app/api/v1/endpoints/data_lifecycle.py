"""
Data Lifecycle and Retention Management API endpoints.

Provides endpoints for:
- Retention policy management
- User consent management
- Data residency controls
- Data export and deletion (GDPR compliance)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....core.security import get_current_user
from ....services.data_lifecycle import (
    data_lifecycle_service,
    DataCategory,
    RetentionPeriod,
    DataResidency,
    ConsentType
)
from ....core.exceptions import DatabaseError, StorageError

router = APIRouter()


class RetentionPolicyRequest(BaseModel):
    """Request model for creating retention policies."""
    data_category: DataCategory = Field(..., description="Category of data")
    retention_period: RetentionPeriod = Field(..., description="Standard retention period")
    custom_days: Optional[int] = Field(None, description="Custom retention period in days")


class ConsentRequest(BaseModel):
    """Request model for managing user consent."""
    consent_type: ConsentType = Field(..., description="Type of consent")
    granted: bool = Field(..., description="Whether consent is granted")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional consent metadata")


class DataResidencyRequest(BaseModel):
    """Request model for setting data residency."""
    residency: DataResidency = Field(..., description="Preferred data residency region")


@router.post("/retention-policies")
async def create_retention_policy(
    request: RetentionPolicyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create or update a retention policy for the current user.
    
    Allows users to customize how long their data is retained.
    """
    try:
        policy_id = await data_lifecycle_service.create_retention_policy(
            user_id=current_user["uid"],
            data_category=request.data_category,
            retention_period=request.retention_period,
            custom_days=request.custom_days
        )
        
        return {
            "policy_id": policy_id,
            "data_category": request.data_category,
            "retention_period": request.retention_period,
            "custom_days": request.custom_days,
            "message": "Retention policy created successfully"
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create retention policy: {str(e)}")


@router.get("/retention-policies")
async def get_retention_policies(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all retention policies for the current user.
    
    Returns the user's custom retention policies and defaults.
    """
    try:
        # Get user data summary which includes retention policies
        summary = await data_lifecycle_service.get_user_data_summary(current_user["uid"])
        
        return {
            "retention_policies": summary["retention_policies"],
            "default_policies": {
                category.value: period.value 
                for category, period in data_lifecycle_service.default_retention_policies.items()
            }
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retention policies: {str(e)}")


@router.post("/consent")
async def manage_consent(
    request: ConsentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Record user consent for data usage.
    
    Manages consent for various data processing activities.
    """
    try:
        consent_id = await data_lifecycle_service.manage_user_consent(
            user_id=current_user["uid"],
            consent_type=request.consent_type,
            granted=request.granted,
            metadata=request.metadata
        )
        
        return {
            "consent_id": consent_id,
            "consent_type": request.consent_type,
            "granted": request.granted,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Consent recorded successfully"
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record consent: {str(e)}")


@router.get("/consent")
async def get_consent_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current consent status for all consent types.
    
    Returns the user's current consent preferences.
    """
    try:
        summary = await data_lifecycle_service.get_user_data_summary(current_user["uid"])
        
        # Check each consent type
        consent_status = {}
        for consent_type in ConsentType:
            consent_status[consent_type.value] = await data_lifecycle_service.check_user_consent(
                current_user["uid"], consent_type
            )
        
        return {
            "consent_status": consent_status,
            "detailed_consents": summary["consents"]
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consent status: {str(e)}")


@router.post("/data-residency")
async def set_data_residency(
    request: DataResidencyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Set data residency preference for the current user.
    
    Controls where user data is stored geographically.
    """
    try:
        await data_lifecycle_service.set_data_residency(
            user_id=current_user["uid"],
            residency=request.residency
        )
        
        return {
            "residency": request.residency,
            "message": "Data residency preference updated successfully"
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set data residency: {str(e)}")


@router.get("/data-summary")
async def get_data_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive summary of user's data and policies.
    
    Provides overview of data storage, retention policies, and consent status.
    """
    try:
        summary = await data_lifecycle_service.get_user_data_summary(current_user["uid"])
        return summary
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data summary: {str(e)}")


@router.post("/export-data")
async def export_user_data(
    current_user: dict = Depends(get_current_user)
):
    """
    Export all user data for GDPR compliance.
    
    Provides complete data export for data portability rights.
    """
    try:
        export_data = await data_lifecycle_service.export_user_data(current_user["uid"])
        
        return {
            "export_data": export_data,
            "export_format": "json",
            "export_version": "1.0",
            "message": "Data export completed successfully"
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.delete("/delete-all-data")
async def delete_all_user_data(
    confirm: bool = Query(..., description="Confirmation that user wants to delete all data"),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete all user data (right to be forgotten).
    
    Permanently removes all user data from the system.
    Requires explicit confirmation.
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Data deletion requires explicit confirmation"
        )
    
    try:
        deletion_counts = await data_lifecycle_service.delete_user_data(current_user["uid"])
        
        return {
            "deletion_counts": deletion_counts,
            "total_items_deleted": sum(deletion_counts.values()),
            "deletion_timestamp": datetime.utcnow().isoformat(),
            "message": "All user data has been permanently deleted"
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user data: {str(e)}")


@router.post("/cleanup-expired")
async def cleanup_expired_data(
    batch_size: int = Query(default=100, ge=1, le=1000, description="Batch size for cleanup"),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger cleanup of expired data.
    
    Allows users to manually clean up their expired data.
    """
    try:
        # Only allow users to clean up their own data
        # In production, this might be an admin-only endpoint
        deletion_counts = await data_lifecycle_service.delete_expired_data(batch_size)
        
        return {
            "deletion_counts": deletion_counts,
            "total_items_deleted": sum(deletion_counts.values()),
            "cleanup_timestamp": datetime.utcnow().isoformat(),
            "message": "Expired data cleanup completed"
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired data: {str(e)}")


@router.get("/available-options")
async def get_available_options():
    """
    Get available options for data lifecycle management.
    
    Returns available data categories, retention periods, residency options, etc.
    """
    return {
        "data_categories": [
            {
                "value": category.value,
                "name": category.value.replace("_", " ").title(),
                "description": f"Data related to {category.value.replace('_', ' ')}"
            }
            for category in DataCategory
        ],
        "retention_periods": [
            {
                "value": period.value,
                "name": period.value.replace("_", " ").title(),
                "days": data_lifecycle_service._get_retention_days(period)
            }
            for period in RetentionPeriod
        ],
        "data_residency_options": [
            {
                "value": residency.value,
                "name": residency.value.upper(),
                "description": f"Store data in {residency.value.upper()} region"
            }
            for residency in DataResidency
        ],
        "consent_types": [
            {
                "value": consent.value,
                "name": consent.value.replace("_", " ").title(),
                "description": f"Consent for {consent.value.replace('_', ' ')}"
            }
            for consent in ConsentType
        ]
    }