"""
Audit Logging and Compliance API endpoints.

Provides endpoints for:
- Audit log querying and analysis
- Compliance reporting
- Security event monitoring
- User activity tracking
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....core.security import get_current_user, require_admin
from ....services.audit_logging import (
    audit_logging_service,
    AuditEventType,
    ComplianceFramework,
    SecurityEventSeverity
)
from ....core.exceptions import AuditError, ComplianceError

router = APIRouter()


class AuditLogQuery(BaseModel):
    """Request model for querying audit logs."""
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    user_id: Optional[str] = Field(None, description="User ID filter")
    event_types: Optional[List[AuditEventType]] = Field(None, description="Event types filter")
    resource_type: Optional[str] = Field(None, description="Resource type filter")
    resource_id: Optional[str] = Field(None, description="Resource ID filter")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")


class SecurityEventRequest(BaseModel):
    """Request model for logging security events."""
    event_type: str = Field(..., description="Type of security event")
    severity: SecurityEventSeverity = Field(..., description="Event severity level")
    description: str = Field(..., description="Event description")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    indicators: Optional[Dict[str, Any]] = Field(None, description="Security indicators")
    auto_mitigate: bool = Field(default=True, description="Whether to attempt automatic mitigation")


class ComplianceReportRequest(BaseModel):
    """Request model for generating compliance reports."""
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    start_date: datetime = Field(..., description="Report period start")
    end_date: datetime = Field(..., description="Report period end")


@router.get("/logs")
async def query_audit_logs(
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    resource_type: Optional[str] = Query(None, description="Resource type filter"),
    resource_id: Optional[str] = Query(None, description="Resource ID filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    current_user: dict = Depends(require_admin)
):
    """
    Query audit logs with filters.
    
    Requires admin privileges.
    """
    try:
        # Convert event_type string to enum if provided
        event_types = None
        if event_type:
            try:
                event_types = [AuditEventType(event_type)]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
        
        # Query audit logs
        logs = await audit_logging_service.query_audit_logs(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            event_types=event_types,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
        
        return {
            "audit_logs": logs,
            "count": len(logs),
            "filters": {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "user_id": user_id,
                "event_type": event_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "limit": limit
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except AuditError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query audit logs: {str(e)}")


@router.get("/logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to query"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit logs for a specific user.
    
    Users can only access their own logs unless they are admin.
    """
    try:
        # Check permissions
        if current_user["uid"] != user_id and not current_user.get("admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Query user's audit logs
        logs = await audit_logging_service.query_audit_logs(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "audit_logs": logs,
            "count": len(logs),
            "period_days": days,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except AuditError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user audit logs: {str(e)}")


@router.get("/activity/user/{user_id}")
async def get_user_activity_summary(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user activity summary.
    
    Users can only access their own activity unless they are admin.
    """
    try:
        # Check permissions
        if current_user["uid"] != user_id and not current_user.get("admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get activity summary
        summary = await audit_logging_service.get_user_activity_summary(user_id, days)
        
        return {
            "activity_summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except AuditError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity summary: {str(e)}")


@router.post("/security-events")
async def log_security_event(
    request: SecurityEventRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Log a security event.
    
    Requires admin privileges.
    """
    try:
        event_id = await audit_logging_service.log_security_event(
            event_type=request.event_type,
            severity=request.severity,
            description=request.description,
            source_ip=request.source_ip,
            user_id=current_user["uid"],
            indicators=request.indicators,
            auto_mitigate=request.auto_mitigate
        )
        
        return {
            "event_id": event_id,
            "event_type": request.event_type,
            "severity": request.severity,
            "logged_at": datetime.utcnow().isoformat(),
            "message": "Security event logged successfully"
        }
        
    except AuditError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log security event: {str(e)}")


@router.get("/security-events")
async def get_security_events(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    severity: Optional[SecurityEventSeverity] = Query(None, description="Severity filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    current_user: dict = Depends(require_admin)
):
    """
    Get recent security events.
    
    Requires admin privileges.
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Build filters
        filters = [("timestamp", ">=", start_time)]
        if severity:
            filters.append(("severity", "==", severity.value))
        
        # Query security events
        from ....services.firestore import FirestoreService
        firestore_service = FirestoreService()
        
        events = await firestore_service.query_documents(
            collection="security_events",
            filters=filters,
            order_by=[("timestamp", "desc")],
            limit=limit
        )
        
        return {
            "security_events": events,
            "count": len(events),
            "time_range_hours": hours,
            "severity_filter": severity.value if severity else None,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security events: {str(e)}")


@router.post("/compliance/reports")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Generate a compliance report.
    
    Requires admin privileges.
    """
    try:
        # Validate date range
        if request.end_date <= request.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Check if date range is not too large (max 1 year)
        if (request.end_date - request.start_date).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Generate compliance report
        report = await audit_logging_service.generate_compliance_report(
            framework=request.framework,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return {
            "compliance_report": report.to_dict(),
            "message": "Compliance report generated successfully"
        }
        
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate compliance report: {str(e)}")


@router.get("/compliance/reports")
async def get_compliance_reports(
    framework: Optional[ComplianceFramework] = Query(None, description="Framework filter"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of results"),
    current_user: dict = Depends(require_admin)
):
    """
    Get existing compliance reports.
    
    Requires admin privileges.
    """
    try:
        # Build filters
        filters = []
        if framework:
            filters.append(("framework", "==", framework.value))
        
        # Query compliance reports
        from ....services.firestore import FirestoreService
        firestore_service = FirestoreService()
        
        reports = await firestore_service.query_documents(
            collection="compliance_reports",
            filters=filters,
            order_by=[("generated_at", "desc")],
            limit=limit
        )
        
        return {
            "compliance_reports": reports,
            "count": len(reports),
            "framework_filter": framework.value if framework else None,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance reports: {str(e)}")


@router.get("/compliance/status")
async def get_compliance_status(
    current_user: dict = Depends(require_admin)
):
    """
    Get current compliance status overview.
    
    Requires admin privileges.
    """
    try:
        # Get recent compliance data (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Generate quick compliance overview for each framework
        compliance_status = {}
        
        for framework in ComplianceFramework:
            try:
                # Get recent audit logs for this framework
                logs = await audit_logging_service.query_audit_logs(
                    start_time=start_date,
                    end_time=end_date,
                    limit=1000
                )
                
                # Filter logs relevant to this framework
                relevant_logs = [
                    log for log in logs
                    if framework.value in log.get("compliance_frameworks", [])
                ]
                
                # Calculate basic compliance metrics
                total_events = len(relevant_logs)
                successful_events = len([log for log in relevant_logs if log.get("result") == "success"])
                compliance_rate = (successful_events / total_events * 100) if total_events > 0 else 100.0
                
                compliance_status[framework.value] = {
                    "total_events": total_events,
                    "successful_events": successful_events,
                    "compliance_rate": compliance_rate,
                    "status": "compliant" if compliance_rate >= 95.0 else "needs_attention"
                }
                
            except Exception as e:
                logger.error(f"Error calculating compliance status for {framework.value}: {e}")
                compliance_status[framework.value] = {
                    "error": str(e),
                    "status": "unknown"
                }
        
        return {
            "compliance_status": compliance_status,
            "period_days": 30,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance status: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_logs(
    batch_size: int = Query(default=100, ge=1, le=1000, description="Batch size for cleanup"),
    current_user: dict = Depends(require_admin)
):
    """
    Clean up expired audit logs.
    
    Requires admin privileges.
    """
    try:
        cleanup_stats = await audit_logging_service.cleanup_expired_logs(batch_size)
        
        return {
            "cleanup_stats": cleanup_stats,
            "total_deleted": sum(cleanup_stats.values()),
            "batch_size": batch_size,
            "cleaned_at": datetime.utcnow().isoformat(),
            "message": "Log cleanup completed successfully"
        }
        
    except AuditError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired logs: {str(e)}")


@router.get("/statistics")
async def get_audit_statistics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(require_admin)
):
    """
    Get audit log statistics.
    
    Requires admin privileges.
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Query audit logs
        logs = await audit_logging_service.query_audit_logs(
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Large limit for statistics
        )
        
        # Calculate statistics
        statistics = {
            "period_days": days,
            "total_events": len(logs),
            "event_types": {},
            "users": {},
            "results": {"success": 0, "failure": 0, "partial": 0},
            "compliance_frameworks": {},
            "daily_activity": {},
            "top_resources": {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Process logs
        for log in logs:
            # Count event types
            event_type = log.get("event_type", "unknown")
            statistics["event_types"][event_type] = statistics["event_types"].get(event_type, 0) + 1
            
            # Count users
            user_id = log.get("user_id", "anonymous")
            statistics["users"][user_id] = statistics["users"].get(user_id, 0) + 1
            
            # Count results
            result = log.get("result", "unknown")
            if result in statistics["results"]:
                statistics["results"][result] += 1
            
            # Count compliance frameworks
            frameworks = log.get("compliance_frameworks", [])
            for framework in frameworks:
                statistics["compliance_frameworks"][framework] = statistics["compliance_frameworks"].get(framework, 0) + 1
            
            # Count daily activity
            timestamp = datetime.fromisoformat(log.get("timestamp"))
            date_key = timestamp.date().isoformat()
            statistics["daily_activity"][date_key] = statistics["daily_activity"].get(date_key, 0) + 1
            
            # Count resource access
            resource_type = log.get("resource_type")
            if resource_type:
                statistics["top_resources"][resource_type] = statistics["top_resources"].get(resource_type, 0) + 1
        
        # Sort top items
        statistics["event_types"] = dict(sorted(statistics["event_types"].items(), key=lambda x: x[1], reverse=True)[:10])
        statistics["users"] = dict(sorted(statistics["users"].items(), key=lambda x: x[1], reverse=True)[:10])
        statistics["top_resources"] = dict(sorted(statistics["top_resources"].items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            "audit_statistics": statistics,
            "message": "Audit statistics generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit statistics: {str(e)}")


@router.get("/event-types")
async def get_available_event_types():
    """
    Get available audit event types.
    
    Public endpoint for reference.
    """
    return {
        "event_types": [
            {
                "value": event_type.value,
                "name": event_type.value.replace("_", " ").title(),
                "description": f"Events related to {event_type.value.replace('_', ' ')}"
            }
            for event_type in AuditEventType
        ],
        "compliance_frameworks": [
            {
                "value": framework.value,
                "name": framework.value.upper(),
                "description": f"{framework.value.upper()} compliance framework"
            }
            for framework in ComplianceFramework
        ],
        "security_severities": [
            {
                "value": severity.value,
                "name": severity.value.title(),
                "description": f"{severity.value.title()} severity security event"
            }
            for severity in SecurityEventSeverity
        ]
    }