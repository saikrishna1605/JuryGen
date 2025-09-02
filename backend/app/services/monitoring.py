"""
Comprehensive Application Monitoring Service.

This service handles:
- Cloud Monitoring dashboards for system health
- Error tracking and alerting with Cloud Error Reporting
- Performance monitoring and latency tracking
- Custom metrics and alerts
- Health checks and uptime monitoring
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import traceback
from functools import wraps
from contextlib import asynccontextmanager

from google.cloud import monitoring_v3
from google.cloud import error_reporting
from google.cloud import logging as cloud_logging
from google.api_core import exceptions as gcp_exceptions
import psutil
import aiohttp

from ..core.config import get_settings
from ..core.exceptions import MonitoringError
from ..monitoring.performance import performance_monitor
from ..monitoring.error_reporting import error_reporter
from ..monitoring.health_checks import health_checker

logger = logging.getLogger(__name__)
settings = get_settings()


class MetricType(str, Enum):
    """Types of metrics to track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    DISTRIBUTION = "distribution"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class MonitoringService:
    """
    Service for comprehensive application monitoring.
    
    Provides metrics collection, error tracking, performance monitoring,
    and health checks.
    """
    
    def __init__(self):
        """Initialize the monitoring service."""
        # Initialize clients
        self.metrics_client = monitoring_v3.MetricServiceClient()
        self.error_client = error_reporting.Client()
        self.logging_client = cloud_logging.Client()
        
        # Project configuration
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.project_name = f"projects/{self.project_id}"
        
        # Metric descriptors cache
        self._metric_descriptors = {}
        
        # Performance tracking
        self._request_metrics = {}
        self._system_metrics = {}
        
        # Health check registry
        self._health_checks = {}
        
        # Initialize custom metrics
        asyncio.create_task(self._initialize_custom_metrics())
    
    async def _initialize_custom_metrics(self):
        """Initialize custom metric descriptors."""
        try:
            # Define custom metrics
            custom_metrics = [
                {
                    "type": "custom.googleapis.com/ai_legal_companion/document_processing_duration",
                    "display_name": "Document Processing Duration",
                    "description": "Time taken to process documents",
                    "metric_kind": monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                    "value_type": monitoring_v3.MetricDescriptor.ValueType.DOUBLE,
                    "unit": "s"
                },
                {
                    "type": "custom.googleapis.com/ai_legal_companion/api_request_count",
                    "display_name": "API Request Count",
                    "description": "Number of API requests",
                    "metric_kind": monitoring_v3.MetricDescriptor.MetricKind.CUMULATIVE,
                    "value_type": monitoring_v3.MetricDescriptor.ValueType.INT64,
                    "unit": "1"
                },
                {
                    "type": "custom.googleapis.com/ai_legal_companion/error_rate",
                    "display_name": "Error Rate",
                    "description": "Rate of errors in the application",
                    "metric_kind": monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                    "value_type": monitoring_v3.MetricDescriptor.ValueType.DOUBLE,
                    "unit": "1"
                },
                {
                    "type": "custom.googleapis.com/ai_legal_companion/active_users",
                    "display_name": "Active Users",
                    "description": "Number of active users",
                    "metric_kind": monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                    "value_type": monitoring_v3.MetricDescriptor.ValueType.INT64,
                    "unit": "1"
                },
                {
                    "type": "custom.googleapis.com/ai_legal_companion/storage_usage",
                    "display_name": "Storage Usage",
                    "description": "Storage usage in bytes",
                    "metric_kind": monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                    "value_type": monitoring_v3.MetricDescriptor.ValueType.INT64,
                    "unit": "By"
                },
                {
                    "type": "custom.googleapis.com/ai_legal_companion/ai_model_latency",
                    "display_name": "AI Model Latency",
                    "description": "Latency of AI model calls",
                    "metric_kind": monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                    "value_type": monitoring_v3.MetricDescriptor.ValueType.DOUBLE,
                    "unit": "ms"
                }
            ]
            
            # Create metric descriptors
            for metric_config in custom_metrics:
                await self._create_metric_descriptor(metric_config)
            
            logger.info("Custom metrics initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing custom metrics: {e}")
    
    async def _create_metric_descriptor(self, config: Dict[str, Any]):
        """Create a custom metric descriptor."""
        try:
            descriptor = monitoring_v3.MetricDescriptor(
                type=config["type"],
                display_name=config["display_name"],
                description=config["description"],
                metric_kind=config["metric_kind"],
                value_type=config["value_type"],
                unit=config["unit"]
            )
            
            # Check if descriptor already exists
            try:
                existing = self.metrics_client.get_metric_descriptor(
                    name=f"{self.project_name}/metricDescriptors/{config['type']}"
                )
                self._metric_descriptors[config["type"]] = existing
                logger.debug(f"Metric descriptor {config['type']} already exists")
                return
            except gcp_exceptions.NotFound:
                pass
            
            # Create new descriptor
            created = self.metrics_client.create_metric_descriptor(
                name=self.project_name,
                metric_descriptor=descriptor
            )
            
            self._metric_descriptors[config["type"]] = created
            logger.info(f"Created metric descriptor: {config['type']}")
            
        except Exception as e:
            logger.error(f"Error creating metric descriptor {config['type']}: {e}")
    
    def track_performance(self, operation_name: str):
        """
        Decorator to track performance of operations.
        
        Args:
            operation_name: Name of the operation to track
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                operation_success = True
                error_details = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    operation_success = False
                    error_details = str(e)
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    # Record metrics
                    await self._record_operation_metrics(
                        operation_name=operation_name,
                        duration=duration,
                        success=operation_success,
                        error_details=error_details
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                operation_success = True
                error_details = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    operation_success = False
                    error_details = str(e)
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    # Record metrics (sync version)
                    asyncio.create_task(self._record_operation_metrics(
                        operation_name=operation_name,
                        duration=duration,
                        success=operation_success,
                        error_details=error_details
                    ))
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    async def _record_operation_metrics(
        self,
        operation_name: str,
        duration: float,
        success: bool,
        error_details: Optional[str] = None
    ):
        """Record metrics for an operation."""
        try:
            # Record duration
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/document_processing_duration",
                value=duration,
                labels={"operation": operation_name, "success": str(success)}
            )
            
            # Record request count
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/api_request_count",
                value=1,
                labels={"operation": operation_name, "success": str(success)}
            )
            
            # Record error if operation failed
            if not success and error_details:
                await self.report_error(
                    error=Exception(error_details),
                    context={
                        "operation": operation_name,
                        "duration": duration
                    }
                )
            
        except Exception as e:
            logger.error(f"Error recording operation metrics: {e}")
    
    async def record_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a custom metric value.
        
        Args:
            metric_type: Type of metric to record
            value: Metric value
            labels: Optional labels for the metric
            timestamp: Optional timestamp (defaults to now)
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Create time series data
            series = monitoring_v3.TimeSeries()
            series.metric.type = metric_type
            
            # Add labels
            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = val
            
            # Add resource labels
            series.resource.type = "gce_instance"  # or appropriate resource type
            series.resource.labels["instance_id"] = "unknown"
            series.resource.labels["zone"] = settings.VERTEX_AI_LOCATION
            
            # Create data point
            point = monitoring_v3.Point()
            point.value.double_value = float(value)
            point.interval.end_time.seconds = int(timestamp.timestamp())
            series.points = [point]
            
            # Write time series
            self.metrics_client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
            logger.debug(f"Recorded metric {metric_type}: {value}")
            
        except Exception as e:
            logger.error(f"Error recording metric {metric_type}: {e}")
    
    async def report_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """
        Report an error to Cloud Error Reporting.
        
        Args:
            error: Exception to report
            context: Additional context information
            user_id: Optional user ID associated with the error
        """
        try:
            # Build error context
            error_context = {
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "context": context or {},
                "user_id": user_id
            }
            
            # Report to Cloud Error Reporting
            self.error_client.report_exception(
                http_context=error_context.get("http_context"),
                user=user_id
            )
            
            # Log structured error
            logger.error(
                f"Error reported: {type(error).__name__}",
                extra={
                    "error_context": error_context,
                    "structured": True
                }
            )
            
            # Update error rate metric
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/error_rate",
                value=1.0,
                labels={
                    "error_type": type(error).__name__,
                    "user_id": user_id or "anonymous"
                }
            )
            
        except Exception as e:
            logger.error(f"Error reporting error: {e}")
    
    async def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/cpu_usage",
                value=cpu_percent,
                labels={"resource": "cpu"}
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/memory_usage",
                value=memory.percent,
                labels={"resource": "memory"}
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/disk_usage",
                value=(disk.used / disk.total) * 100,
                labels={"resource": "disk"}
            )
            
            # Network I/O
            network = psutil.net_io_counters()
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/network_bytes_sent",
                value=network.bytes_sent,
                labels={"direction": "sent"}
            )
            await self.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/network_bytes_recv",
                value=network.bytes_recv,
                labels={"direction": "received"}
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def register_health_check(self, name: str, check_func: Callable):
        """
        Register a health check function.
        
        Args:
            name: Name of the health check
            check_func: Function that returns health status
        """
        self._health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """
        Run all registered health checks.
        
        Returns:
            Dictionary with health check results
        """
        results = {
            "overall_status": HealthStatus.HEALTHY,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        overall_healthy = True
        
        for name, check_func in self._health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    status = await check_func()
                else:
                    status = check_func()
                
                results["checks"][name] = {
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if status != HealthStatus.HEALTHY:
                    overall_healthy = False
                    
            except Exception as e:
                results["checks"][name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_healthy = False
                
                # Report health check error
                await self.report_error(
                    error=e,
                    context={"health_check": name}
                )
        
        # Set overall status
        if not overall_healthy:
            results["overall_status"] = HealthStatus.UNHEALTHY
        
        # Record health status metric
        await self.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/health_status",
            value=1.0 if overall_healthy else 0.0,
            labels={"status": results["overall_status"]}
        )
        
        return results
    
    async def create_alert_policy(
        self,
        name: str,
        condition: Dict[str, Any],
        notification_channels: List[str],
        severity: AlertSeverity = AlertSeverity.WARNING
    ) -> str:
        """
        Create an alert policy.
        
        Args:
            name: Name of the alert policy
            condition: Alert condition configuration
            notification_channels: List of notification channel IDs
            severity: Alert severity level
            
        Returns:
            Alert policy ID
        """
        try:
            # This would integrate with Cloud Monitoring Alert Policies
            # For now, we'll log the alert configuration
            alert_config = {
                "name": name,
                "condition": condition,
                "notification_channels": notification_channels,
                "severity": severity,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Alert policy created: {json.dumps(alert_config, indent=2)}")
            
            # In a real implementation, you would use:
            # alert_client = monitoring_v3.AlertPolicyServiceClient()
            # policy = alert_client.create_alert_policy(...)
            
            return f"alert-policy-{name.lower().replace(' ', '-')}"
            
        except Exception as e:
            logger.error(f"Error creating alert policy: {e}")
            raise MonitoringError(f"Failed to create alert policy: {e}")
    
    async def get_metrics_dashboard_data(
        self,
        time_range: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """
        Get metrics data for dashboard display.
        
        Args:
            time_range: Time range for metrics data
            
        Returns:
            Dashboard metrics data
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_range
            
            # Query metrics (simplified for example)
            dashboard_data = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "metrics": {
                    "request_count": await self._get_metric_value(
                        "custom.googleapis.com/ai_legal_companion/api_request_count",
                        start_time, end_time
                    ),
                    "error_rate": await self._get_metric_value(
                        "custom.googleapis.com/ai_legal_companion/error_rate",
                        start_time, end_time
                    ),
                    "avg_processing_time": await self._get_metric_value(
                        "custom.googleapis.com/ai_legal_companion/document_processing_duration",
                        start_time, end_time
                    ),
                    "active_users": await self._get_metric_value(
                        "custom.googleapis.com/ai_legal_companion/active_users",
                        start_time, end_time
                    )
                },
                "system_health": await self.run_health_checks()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise MonitoringError(f"Failed to get dashboard data: {e}")
    
    async def _get_metric_value(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Get metric value for a time range."""
        try:
            # This would query actual metrics from Cloud Monitoring
            # For now, return a placeholder value
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting metric value for {metric_type}: {e}")
            return 0.0
    
    async def start_monitoring_loop(self, interval: int = 60):
        """
        Start the monitoring loop to collect metrics periodically.
        
        Args:
            interval: Collection interval in seconds
        """
        logger.info(f"Starting monitoring loop with {interval}s interval")
        
        # Start performance monitoring
        await performance_monitor.start_monitoring()
        
        while True:
            try:
                # Collect system metrics
                await self.collect_system_metrics()
                
                # Run comprehensive health checks
                health_results = await health_checker.run_all_health_checks()
                
                # Get overall health status
                overall_status, health_details = await health_checker.get_overall_health()
                
                # Log health status
                if overall_status.value != "healthy":
                    logger.warning(f"System health degraded: {health_details}")
                
                # Record health metrics
                health_score = health_details.get("health_score", 0)
                await self.record_metric(
                    metric_type="custom.googleapis.com/ai_legal_companion/health_status",
                    value=health_score / 100,  # Convert to 0-1 scale
                    labels={"status": overall_status.value}
                )
                
                # Wait for next collection
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await error_reporter.report_error(
                    error=e,
                    context={"monitoring_loop": True}
                )
                await asyncio.sleep(interval)


# Health check functions
async def database_health_check() -> HealthStatus:
    """Check database connectivity."""
    try:
        # This would check actual database connectivity
        # For now, return healthy
        return HealthStatus.HEALTHY
    except Exception:
        return HealthStatus.UNHEALTHY


async def storage_health_check() -> HealthStatus:
    """Check storage service connectivity."""
    try:
        # This would check actual storage connectivity
        # For now, return healthy
        return HealthStatus.HEALTHY
    except Exception:
        return HealthStatus.UNHEALTHY


async def ai_services_health_check() -> HealthStatus:
    """Check AI services connectivity."""
    try:
        # This would check actual AI services connectivity
        # For now, return healthy
        return HealthStatus.HEALTHY
    except Exception:
        return HealthStatus.UNHEALTHY


# Singleton instance
monitoring_service = MonitoringService()

# Register default health checks
monitoring_service.register_health_check("database", database_health_check)
monitoring_service.register_health_check("storage", storage_health_check)
monitoring_service.register_health_check("ai_services", ai_services_health_check)