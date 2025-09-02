"""
Performance Monitoring and Metrics Collection.

Provides comprehensive performance monitoring including:
- Request latency tracking
- Resource usage monitoring
- AI model performance metrics
- System health checks
"""

import time
import psutil
import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from google.cloud import monitoring_v3
from google.cloud import trace_v1

from ..core.config import get_settings
from ..services.monitoring import monitoring_service

settings = get_settings()


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    response_times: Dict[str, float]


@dataclass
class RequestMetrics:
    """Request-level metrics."""
    endpoint: str
    method: str
    status_code: int
    duration: float
    timestamp: datetime
    user_id: Optional[str] = None
    error: Optional[str] = None


class PerformanceMonitor:
    """Monitors system and application performance."""
    
    def __init__(self):
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.trace_client = trace_v1.TraceServiceClient()
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.project_name = f"projects/{self.project_id}"
        
        # Performance tracking
        self._request_metrics: List[RequestMetrics] = []
        self._performance_history: List[PerformanceMetrics] = []
        self._active_requests: Dict[str, float] = {}
        
        # Monitoring state
        self._monitoring_active = False
        self._last_cleanup = datetime.utcnow()
    
    async def start_monitoring(self):
        """Start performance monitoring loop."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        # Start background monitoring tasks
        asyncio.create_task(self._system_metrics_loop())
        asyncio.create_task(self._cleanup_loop())
        
        print("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self._monitoring_active = False
        print("Performance monitoring stopped")
    
    @asynccontextmanager
    async def track_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None
    ):
        """Context manager to track request performance."""
        request_id = f"{endpoint}_{method}_{time.time()}"
        start_time = time.time()
        
        self._active_requests[request_id] = start_time
        
        try:
            yield
            
            # Request completed successfully
            duration = time.time() - start_time
            
            metrics = RequestMetrics(
                endpoint=endpoint,
                method=method,
                status_code=200,
                duration=duration,
                timestamp=datetime.utcnow(),
                user_id=user_id
            )
            
            await self._record_request_metrics(metrics)
            
        except Exception as e:
            # Request failed
            duration = time.time() - start_time
            
            metrics = RequestMetrics(
                endpoint=endpoint,
                method=method,
                status_code=500,
                duration=duration,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                error=str(e)
            )
            
            await self._record_request_metrics(metrics)
            raise
            
        finally:
            self._active_requests.pop(request_id, None)
    
    async def track_ai_model_latency(
        self,
        model_name: str,
        operation: str,
        latency_ms: float
    ):
        """Track AI model performance metrics."""
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/ai_model_latency",
            value=latency_ms,
            labels={
                "model_name": model_name,
                "operation": operation
            }
        )
    
    async def track_document_processing(
        self,
        document_type: str,
        processing_stage: str,
        duration_seconds: float
    ):
        """Track document processing performance."""
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/document_processing_duration",
            value=duration_seconds,
            labels={
                "document_type": document_type,
                "processing_stage": processing_stage
            }
        )
    
    async def get_system_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics."""
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Active connections
        connections = len(psutil.net_connections())
        
        # Response times (average from recent requests)
        response_times = self._calculate_response_times()
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            active_connections=connections,
            response_times=response_times
        )
    
    async def get_performance_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_requests = [
            r for r in self._request_metrics
            if r.timestamp >= cutoff_time
        ]
        
        recent_performance = [
            p for p in self._performance_history
            if p.timestamp >= cutoff_time
        ]
        
        if not recent_requests or not recent_performance:
            return {
                "period_hours": hours,
                "total_requests": 0,
                "error_rate": 0,
                "avg_response_time": 0,
                "system_health": "unknown"
            }
        
        # Calculate request metrics
        total_requests = len(recent_requests)
        error_requests = len([r for r in recent_requests if r.status_code >= 400])
        error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
        
        avg_response_time = sum(r.duration for r in recent_requests) / total_requests
        
        # Calculate system metrics
        avg_cpu = sum(p.cpu_usage for p in recent_performance) / len(recent_performance)
        avg_memory = sum(p.memory_usage for p in recent_performance) / len(recent_performance)
        
        # Determine system health
        system_health = "healthy"
        if avg_cpu > 80 or avg_memory > 85 or error_rate > 5:
            system_health = "degraded"
        if avg_cpu > 90 or avg_memory > 95 or error_rate > 10:
            system_health = "unhealthy"
        
        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "avg_cpu_usage": avg_cpu,
            "avg_memory_usage": avg_memory,
            "system_health": system_health,
            "top_endpoints": self._get_top_endpoints(recent_requests),
            "slowest_endpoints": self._get_slowest_endpoints(recent_requests)
        }
    
    async def _system_metrics_loop(self):
        """Background loop to collect system metrics."""
        while self._monitoring_active:
            try:
                metrics = await self.get_system_metrics()
                self._performance_history.append(metrics)
                
                # Record metrics to Cloud Monitoring
                await self._record_system_metrics(metrics)
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self._performance_history = [
                    p for p in self._performance_history
                    if p.timestamp >= cutoff_time
                ]
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                print(f"Error in system metrics loop: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Background loop to clean up old data."""
        while self._monitoring_active:
            try:
                now = datetime.utcnow()
                
                # Clean up every hour
                if now - self._last_cleanup > timedelta(hours=1):
                    await self._cleanup_old_data()
                    self._last_cleanup = now
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)
    
    async def _record_request_metrics(self, metrics: RequestMetrics):
        """Record request metrics."""
        self._request_metrics.append(metrics)
        
        # Record to Cloud Monitoring
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/api_request_count",
            value=1,
            labels={
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "status_code": str(metrics.status_code)
            }
        )
        
        # Record error rate if applicable
        if metrics.status_code >= 400:
            error_type = "client_error" if metrics.status_code < 500 else "server_error"
            
            await monitoring_service.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/error_rate",
                value=1,
                labels={
                    "error_type": error_type,
                    "service": "api"
                }
            )
    
    async def _record_system_metrics(self, metrics: PerformanceMetrics):
        """Record system metrics to Cloud Monitoring."""
        # CPU usage
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/cpu_usage",
            value=metrics.cpu_usage
        )
        
        # Memory usage
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/memory_usage",
            value=metrics.memory_usage
        )
        
        # Active users (approximate from active requests)
        active_users = len(set(
            r.user_id for r in self._request_metrics[-100:]  # Last 100 requests
            if r.user_id and r.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ))
        
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/active_users",
            value=active_users
        )
        
        # Health status
        health_status = 1.0
        if metrics.cpu_usage > 90 or metrics.memory_usage > 95:
            health_status = 0.0
        elif metrics.cpu_usage > 80 or metrics.memory_usage > 85:
            health_status = 0.5
        
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/health_status",
            value=health_status
        )
    
    def _calculate_response_times(self) -> Dict[str, float]:
        """Calculate average response times by endpoint."""
        if not self._request_metrics:
            return {}
        
        # Get recent requests (last 5 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        recent_requests = [
            r for r in self._request_metrics
            if r.timestamp >= cutoff_time
        ]
        
        if not recent_requests:
            return {}
        
        # Group by endpoint
        endpoint_times = {}
        for request in recent_requests:
            if request.endpoint not in endpoint_times:
                endpoint_times[request.endpoint] = []
            endpoint_times[request.endpoint].append(request.duration)
        
        # Calculate averages
        return {
            endpoint: sum(times) / len(times)
            for endpoint, times in endpoint_times.items()
        }
    
    def _get_top_endpoints(self, requests: List[RequestMetrics]) -> List[Dict[str, Any]]:
        """Get top endpoints by request count."""
        endpoint_counts = {}
        
        for request in requests:
            key = f"{request.method} {request.endpoint}"
            endpoint_counts[key] = endpoint_counts.get(key, 0) + 1
        
        return [
            {"endpoint": endpoint, "count": count}
            for endpoint, count in sorted(
                endpoint_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]
    
    def _get_slowest_endpoints(self, requests: List[RequestMetrics]) -> List[Dict[str, Any]]:
        """Get slowest endpoints by average response time."""
        endpoint_times = {}
        
        for request in requests:
            key = f"{request.method} {request.endpoint}"
            if key not in endpoint_times:
                endpoint_times[key] = []
            endpoint_times[key].append(request.duration)
        
        endpoint_averages = {
            endpoint: sum(times) / len(times)
            for endpoint, times in endpoint_times.items()
        }
        
        return [
            {"endpoint": endpoint, "avg_duration": duration}
            for endpoint, duration in sorted(
                endpoint_averages.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]
    
    async def _cleanup_old_data(self):
        """Clean up old performance data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Clean up request metrics
        self._request_metrics = [
            r for r in self._request_metrics
            if r.timestamp >= cutoff_time
        ]
        
        # Clean up performance history
        self._performance_history = [
            p for p in self._performance_history
            if p.timestamp >= cutoff_time
        ]
        
        print(f"Cleaned up old performance data. "
              f"Requests: {len(self._request_metrics)}, "
              f"Performance: {len(self._performance_history)}")


# Singleton instance
performance_monitor = PerformanceMonitor()