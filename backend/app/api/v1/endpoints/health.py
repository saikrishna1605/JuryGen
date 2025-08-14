"""
Health check endpoints.
"""

from fastapi import APIRouter
from app.models.base import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns:
        HealthCheck: Service health status
    """
    return HealthCheck.healthy(version="1.0.0")


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with service dependencies.
    
    Returns:
        dict: Detailed health information
    """
    # TODO: Add checks for dependent services
    # - Firebase connection
    # - Google Cloud services
    # - Database connectivity
    
    services = {
        "database": {
            "status": "up",
            "response_time": 0.001,
            "last_check": "2023-11-05T10:00:00Z"
        },
        "ai_services": {
            "status": "up", 
            "response_time": 0.050,
            "last_check": "2023-11-05T10:00:00Z"
        },
        "storage": {
            "status": "up",
            "response_time": 0.010,
            "last_check": "2023-11-05T10:00:00Z"
        }
    }
    
    return HealthCheck.healthy(version="1.0.0").model_copy(
        update={"services": services}
    )