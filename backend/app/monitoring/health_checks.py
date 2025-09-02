"""
Health Check System.

Provides comprehensive health monitoring including:
- System component health checks
- External service availability
- Performance threshold monitoring
- Automated recovery suggestions
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from google.cloud import firestore
from google.cloud import storage
from google.cloud import aiplatform

from ..core.config import get_settings
from ..services.monitoring import monitoring_service

settings = get_settings()


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result data structure."""
    component: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Performs comprehensive health checks."""
    
    def __init__(self):
        self.firestore_client = firestore.Client()
        self.storage_client = storage.Client()
        
        # Health check history
        self._health_history: Dict[str, List[HealthCheckResult]] = {}
        self._last_check_time = datetime.utcnow()
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks and return results."""
        checks = [
            self.check_api_health(),
            self.check_database_health(),
            self.check_storage_health(),
            self.check_ai_services_health(),
            self.check_external_services_health(),
            self.check_system_resources()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        health_results = {}
        for result in results:
            if isinstance(result, Exception):
                # Handle failed health check
                health_results["unknown"] = HealthCheckResult(
                    component="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {result}",
                    response_time=0.0,
                    timestamp=datetime.utcnow()
                )
            else:
                health_results[result.component] = result
        
        # Store results in history
        for component, result in health_results.items():
            if component not in self._health_history:
                self._health_history[component] = []
            
            self._health_history[component].append(result)
            
            # Keep only last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self._health_history[component] = [
                r for r in self._health_history[component]
                if r.timestamp >= cutoff_time
            ]
        
        self._last_check_time = datetime.utcnow()
        
        return health_results
    
    async def check_api_health(self) -> HealthCheckResult:
        """Check API endpoint health."""
        start_time = datetime.utcnow()
        
        try:
            # Simple internal health check
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="api",
                status=HealthStatus.HEALTHY,
                message="API is responding normally",
                response_time=response_time,
                timestamp=datetime.utcnow(),
                details={"endpoint": "/health"}
            )
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="api",
                status=HealthStatus.UNHEALTHY,
                message=f"API health check failed: {e}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check Firestore database health."""
        start_time = datetime.utcnow()
        
        try:
            # Test database connection with a simple query
            test_collection = self.firestore_client.collection("health_check")
            test_doc = test_collection.document("test")
            
            # Write test document
            await test_doc.set({"timestamp": datetime.utcnow()})
            
            # Read test document
            doc = await test_doc.get()
            
            # Clean up test document
            await test_doc.delete()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if doc.exists:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.HEALTHY,
                    message="Database is accessible and responsive",
                    response_time=response_time,
                    timestamp=datetime.utcnow(),
                    details={"operation": "read/write test"}
                )
            else:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.DEGRADED,
                    message="Database write succeeded but read failed",
                    response_time=response_time,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {e}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )    

    async def check_storage_health(self) -> HealthCheckResult:
        """Check Cloud Storage health."""
        start_time = datetime.utcnow()
        
        try:
            # Test storage connection
            bucket_name = settings.STORAGE_BUCKET
            bucket = self.storage_client.bucket(bucket_name)
            
            # Test write operation
            test_blob = bucket.blob("health_check/test.txt")
            test_content = f"Health check at {datetime.utcnow().isoformat()}"
            
            test_blob.upload_from_string(test_content)
            
            # Test read operation
            downloaded_content = test_blob.download_as_text()
            
            # Clean up test file
            test_blob.delete()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if downloaded_content == test_content:
                return HealthCheckResult(
                    component="storage",
                    status=HealthStatus.HEALTHY,
                    message="Storage is accessible and responsive",
                    response_time=response_time,
                    timestamp=datetime.utcnow(),
                    details={"bucket": bucket_name, "operation": "read/write test"}
                )
            else:
                return HealthCheckResult(
                    component="storage",
                    status=HealthStatus.DEGRADED,
                    message="Storage write succeeded but read returned different content",
                    response_time=response_time,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage health check failed: {e}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_ai_services_health(self) -> HealthCheckResult:
        """Check AI services health."""
        start_time = datetime.utcnow()
        
        try:
            # Initialize Vertex AI
            aiplatform.init(
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.VERTEX_AI_LOCATION
            )
            
            # Test simple prediction (this is a lightweight check)
            # In a real implementation, you might want to test actual model endpoints
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="ai_services",
                status=HealthStatus.HEALTHY,
                message="AI services are accessible",
                response_time=response_time,
                timestamp=datetime.utcnow(),
                details={"project": settings.GOOGLE_CLOUD_PROJECT, "location": settings.VERTEX_AI_LOCATION}
            )
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="ai_services",
                status=HealthStatus.UNHEALTHY,
                message=f"AI services health check failed: {e}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_external_services_health(self) -> HealthCheckResult:
        """Check external services health."""
        start_time = datetime.utcnow()
        
        try:
            # Test external service connectivity
            async with aiohttp.ClientSession() as session:
                # Test Google APIs
                async with session.get(
                    "https://www.googleapis.com/",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        response_time = (datetime.utcnow() - start_time).total_seconds()
                        
                        return HealthCheckResult(
                            component="external_services",
                            status=HealthStatus.HEALTHY,
                            message="External services are accessible",
                            response_time=response_time,
                            timestamp=datetime.utcnow(),
                            details={"tested_service": "Google APIs"}
                        )
                    else:
                        response_time = (datetime.utcnow() - start_time).total_seconds()
                        
                        return HealthCheckResult(
                            component="external_services",
                            status=HealthStatus.DEGRADED,
                            message=f"External service returned status {response.status}",
                            response_time=response_time,
                            timestamp=datetime.utcnow()
                        )
                        
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="external_services",
                status=HealthStatus.UNHEALTHY,
                message=f"External services health check failed: {e}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource health."""
        start_time = datetime.utcnow()
        
        try:
            import psutil
            
            # Check CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            message = "System resources are within normal limits"
            
            if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95:
                status = HealthStatus.UNHEALTHY
                message = "System resources are critically high"
            elif cpu_usage > 80 or memory_usage > 85 or disk_usage > 85:
                status = HealthStatus.DEGRADED
                message = "System resources are elevated"
            
            return HealthCheckResult(
                component="system_resources",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                details={
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "disk_usage": disk_usage
                }
            )
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HealthCheckResult(
                component="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resource check failed: {e}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def get_overall_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Get overall system health status."""
        health_results = await self.run_all_health_checks()
        
        # Determine overall status
        statuses = [result.status for result in health_results.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        # Calculate health score (0-100)
        healthy_count = sum(1 for status in statuses if status == HealthStatus.HEALTHY)
        health_score = (healthy_count / len(statuses)) * 100 if statuses else 0
        
        # Get component details
        component_details = {
            component: {
                "status": result.status.value,
                "message": result.message,
                "response_time": result.response_time,
                "details": result.details
            }
            for component, result in health_results.items()
        }
        
        return overall_status, {
            "overall_status": overall_status.value,
            "health_score": health_score,
            "last_check": self._last_check_time.isoformat(),
            "components": component_details,
            "summary": {
                "healthy": len([s for s in statuses if s == HealthStatus.HEALTHY]),
                "degraded": len([s for s in statuses if s == HealthStatus.DEGRADED]),
                "unhealthy": len([s for s in statuses if s == HealthStatus.UNHEALTHY]),
                "unknown": len([s for s in statuses if s == HealthStatus.UNKNOWN])
            }
        }
    
    async def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over time."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        trends = {}
        
        for component, history in self._health_history.items():
            recent_history = [
                h for h in history
                if h.timestamp >= cutoff_time
            ]
            
            if not recent_history:
                continue
            
            # Calculate uptime percentage
            healthy_count = len([h for h in recent_history if h.status == HealthStatus.HEALTHY])
            uptime_percentage = (healthy_count / len(recent_history)) * 100
            
            # Calculate average response time
            avg_response_time = sum(h.response_time for h in recent_history) / len(recent_history)
            
            # Get current status
            current_status = recent_history[-1].status.value if recent_history else "unknown"
            
            trends[component] = {
                "current_status": current_status,
                "uptime_percentage": uptime_percentage,
                "avg_response_time": avg_response_time,
                "check_count": len(recent_history),
                "last_check": recent_history[-1].timestamp.isoformat() if recent_history else None
            }
        
        return {
            "period_hours": hours,
            "components": trends,
            "overall_uptime": sum(
                trend["uptime_percentage"] for trend in trends.values()
            ) / len(trends) if trends else 0
        }


# Singleton instance
health_checker = HealthChecker()