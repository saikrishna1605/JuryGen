"""
Monitoring API endpoints.

Provides endpoints for:
- System health checks
- Performance metrics
- Error reporting and tracking
- Monitoring dashboard data
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ....core.auth import get_current_user
from ....services.monitoring import monitoring_service
from ....monitoring.performance import performance_monitor
from ....monitoring.error_reporting import error_reporter
from ....monitoring.health_checks import health_checker

router = APIRouter()


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    overall_status: str
    health_score: float
    last_check: str
    components: Dict[str, Any]
    summary: Dict[str, int]


class PerformanceSummaryResponse(BaseModel):
    """Performance summary response model."""
    period_hours: int
    total_requests: int
    error_rate: float
    avg_response_time: float
    avg_cpu_usage: float
    avg_memory_usage: float
    system_health: str
    top_endpoints: List[Dict[str, Any]]
    slowest_endpoints: List[Dict[str, Any]]


class ErrorSummaryResponse(BaseModel):
    """Error summary response model."""
    period_hours: int
    total_errors: int
    category_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    top_errors: List[Dict[str, Any]]
    critical_errors: int


@router.get("/health", response_model=HealthCheckResponse)
async def get_system_health():
    """Get comprehensive system health status."""
    try:
        overall_status, health_details = await health_checker.get_overall_health()
        
        return HealthCheckResponse(
            overall_status=health_details["overall_status"],
            health_score=health_details["health_score"],
            last_check=health_details["last_check"],
            components=health_details["components"],
            summary=health_details["summary"]
        )
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/health"}
        )
        raise HTTPException(status_code=500, detail="Failed to get health status")


@router.get("/health/trends")
async def get_health_trends(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to include")
):
    """Get health trends over time."""
    try:
        trends = await health_checker.get_health_trends(hours=hours)
        return trends
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/health/trends", "hours": hours}
        )
        raise HTTPException(status_code=500, detail="Failed to get health trends")


@router.get("/performance", response_model=PerformanceSummaryResponse)
async def get_performance_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to include")
):
    """Get performance summary and metrics."""
    try:
        summary = await performance_monitor.get_performance_summary(hours=hours)
        
        return PerformanceSummaryResponse(
            period_hours=summary["period_hours"],
            total_requests=summary["total_requests"],
            error_rate=summary["error_rate"],
            avg_response_time=summary["avg_response_time"],
            avg_cpu_usage=summary["avg_cpu_usage"],
            avg_memory_usage=summary["avg_memory_usage"],
            system_health=summary["system_health"],
            top_endpoints=summary["top_endpoints"],
            slowest_endpoints=summary["slowest_endpoints"]
        )
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/performance", "hours": hours}
        )
        raise HTTPException(status_code=500, detail="Failed to get performance summary")


@router.get("/errors", response_model=ErrorSummaryResponse)
async def get_error_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to include")
):
    """Get error summary and trends."""
    try:
        summary = await error_reporter.get_error_summary(hours=hours)
        
        return ErrorSummaryResponse(
            period_hours=summary["period_hours"],
            total_errors=summary["total_errors"],
            category_breakdown=summary["category_breakdown"],
            severity_breakdown=summary["severity_breakdown"],
            top_errors=summary["top_errors"],
            critical_errors=summary["critical_errors"]
        )
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/errors", "hours": hours}
        )
        raise HTTPException(status_code=500, detail="Failed to get error summary")


@router.get("/metrics/system")
async def get_system_metrics():
    """Get current system metrics."""
    try:
        metrics = await performance_monitor.get_system_metrics()
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "active_connections": metrics.active_connections,
            "response_times": metrics.response_times
        }
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/metrics/system"}
        )
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/dashboard")
async def get_dashboard_data(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to include")
):
    """Get comprehensive dashboard data."""
    try:
        # Get all monitoring data
        health_status, health_details = await health_checker.get_overall_health()
        performance_summary = await performance_monitor.get_performance_summary(hours=hours)
        error_summary = await error_reporter.get_error_summary(hours=hours)
        system_metrics = await performance_monitor.get_system_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "health": {
                "overall_status": health_details["overall_status"],
                "health_score": health_details["health_score"],
                "components": health_details["components"],
                "summary": health_details["summary"]
            },
            "performance": {
                "total_requests": performance_summary["total_requests"],
                "error_rate": performance_summary["error_rate"],
                "avg_response_time": performance_summary["avg_response_time"],
                "system_health": performance_summary["system_health"],
                "top_endpoints": performance_summary["top_endpoints"][:5],
                "slowest_endpoints": performance_summary["slowest_endpoints"][:5]
            },
            "errors": {
                "total_errors": error_summary["total_errors"],
                "critical_errors": error_summary["critical_errors"],
                "category_breakdown": error_summary["category_breakdown"],
                "severity_breakdown": error_summary["severity_breakdown"]
            },
            "system": {
                "cpu_usage": system_metrics.cpu_usage,
                "memory_usage": system_metrics.memory_usage,
                "disk_usage": system_metrics.disk_usage,
                "active_connections": system_metrics.active_connections
            }
        }
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/dashboard", "hours": hours}
        )
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.post("/test-error")
async def test_error_reporting(
    current_user = Depends(get_current_user)
):
    """Test endpoint for error reporting (development only)."""
    try:
        # Create a test error
        test_error = Exception("Test error for monitoring system verification")
        
        await error_reporter.report_error(
            error=test_error,
            context={
                "test": True,
                "endpoint": "/monitoring/test-error",
                "user_action": "manual_test"
            },
            user_id=current_user.get("uid")
        )
        
        return {
            "message": "Test error reported successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to report test error: {e}")


@router.get("/alerts")
async def get_active_alerts():
    """Get active monitoring alerts."""
    try:
        # This would integrate with actual alerting system
        # For now, return placeholder data
        return {
            "active_alerts": [],
            "alert_count": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/alerts"}
        )
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.get("/uptime")
async def get_uptime_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to include")
):
    """Get system uptime statistics."""
    try:
        trends = await health_checker.get_health_trends(hours=hours)
        
        return {
            "period_hours": hours,
            "overall_uptime": trends["overall_uptime"],
            "components": trends["components"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        await error_reporter.report_error(
            error=e,
            context={"endpoint": "/monitoring/uptime", "hours": hours}
        )
        raise HTTPException(status_code=500, detail="Failed to get uptime stats")