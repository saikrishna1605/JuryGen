"""
Tests for Monitoring and Observability Service.

Tests cover:
- Performance tracking and metrics collection
- Error reporting and alerting
- Health checks and system monitoring
- Custom metrics and dashboards
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.monitoring import (
    MonitoringService,
    MetricType,
    AlertSeverity,
    HealthStatus
)
from app.core.exceptions import MonitoringError


@pytest.fixture
def mock_metrics_client():
    """Mock Cloud Monitoring client."""
    mock = Mock()
    return mock


@pytest.fixture
def mock_error_client():
    """Mock Cloud Error Reporting client."""
    mock = Mock()
    return mock


@pytest.fixture
def mock_logging_client():
    """Mock Cloud Logging client."""
    mock = Mock()
    return mock


@pytest.fixture
def monitoring_service(mock_metrics_client, mock_error_client, mock_logging_client):
    """Create MonitoringService with mocked dependencies."""
    service = MonitoringService()
    service.metrics_client = mock_metrics_client
    service.error_client = mock_error_client
    service.logging_client = mock_logging_client
    return service


@pytest.fixture
def sample_error():
    """Sample error for testing."""
    return ValueError("Test error message")


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        "operation": "document_processing",
        "user_id": "test-user-123",
        "document_id": "doc-456"
    }


class TestPerformanceTracking:
    """Test performance tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_performance_decorator_async_success(self, monitoring_service):
        """Test performance tracking decorator for successful async operations."""
        
        @monitoring_service.track_performance("test_operation")
        async def test_async_function():
            await asyncio.sleep(0.1)  # Simulate work
            return "success"
        
        # Mock the metric recording
        monitoring_service._record_operation_metrics = AsyncMock()
        
        # Execute function
        result = await test_async_function()
        
        # Assert
        assert result == "success"
        monitoring_service._record_operation_metrics.assert_called_once()
        call_args = monitoring_service._record_operation_metrics.call_args[1]
        assert call_args["operation_name"] == "test_operation"
        assert call_args["success"] is True
        assert call_args["duration"] >= 0.1
        assert call_args["error_details"] is None

    @pytest.mark.asyncio
    async def test_track_performance_decorator_async_failure(self, monitoring_service):
        """Test performance tracking decorator for failed async operations."""
        
        @monitoring_service.track_performance("test_operation")
        async def test_async_function():
            await asyncio.sleep(0.05)
            raise ValueError("Test error")
        
        # Mock the metric recording
        monitoring_service._record_operation_metrics = AsyncMock()
        
        # Execute function and expect error
        with pytest.raises(ValueError, match="Test error"):
            await test_async_function()
        
        # Assert metrics were recorded
        monitoring_service._record_operation_metrics.assert_called_once()
        call_args = monitoring_service._record_operation_metrics.call_args[1]
        assert call_args["operation_name"] == "test_operation"
        assert call_args["success"] is False
        assert call_args["error_details"] == "Test error"

    def test_track_performance_decorator_sync_success(self, monitoring_service):
        """Test performance tracking decorator for successful sync operations."""
        
        @monitoring_service.track_performance("sync_operation")
        def test_sync_function():
            time.sleep(0.05)  # Simulate work
            return "sync_success"
        
        # Mock the metric recording
        monitoring_service._record_operation_metrics = AsyncMock()
        
        # Execute function
        result = test_sync_function()
        
        # Assert
        assert result == "sync_success"
        # Note: For sync functions, the metric recording is scheduled as a task

    @pytest.mark.asyncio
    async def test_record_operation_metrics(self, monitoring_service):
        """Test recording operation metrics."""
        # Mock dependencies
        monitoring_service.record_metric = AsyncMock()
        monitoring_service.report_error = AsyncMock()
        
        # Test successful operation
        await monitoring_service._record_operation_metrics(
            operation_name="test_op",
            duration=1.5,
            success=True,
            error_details=None
        )
        
        # Assert metrics were recorded
        assert monitoring_service.record_metric.call_count == 2  # duration + count
        monitoring_service.report_error.assert_not_called()
        
        # Test failed operation
        monitoring_service.record_metric.reset_mock()
        await monitoring_service._record_operation_metrics(
            operation_name="test_op",
            duration=2.0,
            success=False,
            error_details="Test error"
        )
        
        # Assert error was reported
        monitoring_service.report_error.assert_called_once()


class TestMetricsRecording:
    """Test metrics recording functionality."""

    @pytest.mark.asyncio
    async def test_record_metric_success(self, monitoring_service, mock_metrics_client):
        """Test successful metric recording."""
        # Mock the client
        mock_metrics_client.create_time_series = Mock()
        
        # Record metric
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/test_metric",
            value=42.5,
            labels={"operation": "test", "status": "success"}
        )
        
        # Assert
        mock_metrics_client.create_time_series.assert_called_once()
        call_args = mock_metrics_client.create_time_series.call_args
        assert call_args[1]["name"] == monitoring_service.project_name
        assert len(call_args[1]["time_series"]) == 1
        
        time_series = call_args[1]["time_series"][0]
        assert time_series.metric.type == "custom.googleapis.com/test_metric"
        assert time_series.metric.labels["operation"] == "test"
        assert time_series.metric.labels["status"] == "success"
        assert time_series.points[0].value.double_value == 42.5

    @pytest.mark.asyncio
    async def test_record_metric_with_timestamp(self, monitoring_service, mock_metrics_client):
        """Test metric recording with custom timestamp."""
        # Mock the client
        mock_metrics_client.create_time_series = Mock()
        
        # Custom timestamp
        custom_time = datetime.utcnow() - timedelta(hours=1)
        
        # Record metric
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/test_metric",
            value=100.0,
            timestamp=custom_time
        )
        
        # Assert timestamp was used
        mock_metrics_client.create_time_series.assert_called_once()
        time_series = mock_metrics_client.create_time_series.call_args[1]["time_series"][0]
        assert time_series.points[0].interval.end_time.seconds == int(custom_time.timestamp())

    @pytest.mark.asyncio
    async def test_record_metric_error_handling(self, monitoring_service, mock_metrics_client):
        """Test metric recording error handling."""
        # Mock client to raise exception
        mock_metrics_client.create_time_series.side_effect = Exception("Metrics API error")
        
        # Record metric (should not raise exception)
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/test_metric",
            value=50.0
        )
        
        # Should have attempted to record
        mock_metrics_client.create_time_series.assert_called_once()


class TestErrorReporting:
    """Test error reporting functionality."""

    @pytest.mark.asyncio
    async def test_report_error_success(self, monitoring_service, mock_error_client, sample_error, sample_context):
        """Test successful error reporting."""
        # Mock dependencies
        mock_error_client.report_exception = Mock()
        monitoring_service.record_metric = AsyncMock()
        
        # Report error
        await monitoring_service.report_error(
            error=sample_error,
            context=sample_context,
            user_id="test-user-123"
        )
        
        # Assert error was reported
        mock_error_client.report_exception.assert_called_once()
        call_args = mock_error_client.report_exception.call_args[1]
        assert call_args["user"] == "test-user-123"
        
        # Assert metric was recorded
        monitoring_service.record_metric.assert_called_once()
        metric_call = monitoring_service.record_metric.call_args[1]
        assert metric_call["metric_type"] == "custom.googleapis.com/ai_legal_companion/error_rate"
        assert metric_call["value"] == 1.0
        assert metric_call["labels"]["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_report_error_without_user(self, monitoring_service, mock_error_client, sample_error):
        """Test error reporting without user ID."""
        # Mock dependencies
        mock_error_client.report_exception = Mock()
        monitoring_service.record_metric = AsyncMock()
        
        # Report error without user
        await monitoring_service.report_error(error=sample_error)
        
        # Assert error was reported
        mock_error_client.report_exception.assert_called_once()
        call_args = mock_error_client.report_exception.call_args[1]
        assert call_args["user"] is None
        
        # Assert metric labels
        metric_call = monitoring_service.record_metric.call_args[1]
        assert metric_call["labels"]["user_id"] == "anonymous"

    @pytest.mark.asyncio
    async def test_report_error_exception_handling(self, monitoring_service, mock_error_client, sample_error):
        """Test error reporting when reporting itself fails."""
        # Mock client to raise exception
        mock_error_client.report_exception.side_effect = Exception("Reporting failed")
        monitoring_service.record_metric = AsyncMock()
        
        # Report error (should not raise exception)
        await monitoring_service.report_error(error=sample_error)
        
        # Should have attempted to report
        mock_error_client.report_exception.assert_called_once()


class TestHealthChecks:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_register_health_check(self, monitoring_service):
        """Test registering a health check."""
        def test_check():
            return HealthStatus.HEALTHY
        
        # Register check
        monitoring_service.register_health_check("test_service", test_check)
        
        # Assert check was registered
        assert "test_service" in monitoring_service._health_checks
        assert monitoring_service._health_checks["test_service"] == test_check

    @pytest.mark.asyncio
    async def test_run_health_checks_all_healthy(self, monitoring_service):
        """Test running health checks when all are healthy."""
        # Mock health checks
        def healthy_check():
            return HealthStatus.HEALTHY
        
        async def async_healthy_check():
            return HealthStatus.HEALTHY
        
        monitoring_service.register_health_check("sync_service", healthy_check)
        monitoring_service.register_health_check("async_service", async_healthy_check)
        
        # Mock metric recording
        monitoring_service.record_metric = AsyncMock()
        
        # Run health checks
        results = await monitoring_service.run_health_checks()
        
        # Assert results
        assert results["overall_status"] == HealthStatus.HEALTHY
        assert len(results["checks"]) == 2
        assert results["checks"]["sync_service"]["status"] == HealthStatus.HEALTHY
        assert results["checks"]["async_service"]["status"] == HealthStatus.HEALTHY
        
        # Assert metric was recorded
        monitoring_service.record_metric.assert_called_once()
        metric_call = monitoring_service.record_metric.call_args[1]
        assert metric_call["value"] == 1.0  # Healthy

    @pytest.mark.asyncio
    async def test_run_health_checks_with_failures(self, monitoring_service):
        """Test running health checks with some failures."""
        # Mock health checks
        def healthy_check():
            return HealthStatus.HEALTHY
        
        def unhealthy_check():
            return HealthStatus.UNHEALTHY
        
        def failing_check():
            raise Exception("Check failed")
        
        monitoring_service.register_health_check("healthy_service", healthy_check)
        monitoring_service.register_health_check("unhealthy_service", unhealthy_check)
        monitoring_service.register_health_check("failing_service", failing_check)
        
        # Mock dependencies
        monitoring_service.record_metric = AsyncMock()
        monitoring_service.report_error = AsyncMock()
        
        # Run health checks
        results = await monitoring_service.run_health_checks()
        
        # Assert results
        assert results["overall_status"] == HealthStatus.UNHEALTHY
        assert results["checks"]["healthy_service"]["status"] == HealthStatus.HEALTHY
        assert results["checks"]["unhealthy_service"]["status"] == HealthStatus.UNHEALTHY
        assert results["checks"]["failing_service"]["status"] == HealthStatus.UNHEALTHY
        assert "error" in results["checks"]["failing_service"]
        
        # Assert error was reported for failing check
        monitoring_service.report_error.assert_called_once()
        
        # Assert metric shows unhealthy
        metric_call = monitoring_service.record_metric.call_args[1]
        assert metric_call["value"] == 0.0  # Unhealthy


class TestSystemMetrics:
    """Test system metrics collection."""

    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    async def test_collect_system_metrics(
        self, 
        mock_net_io, 
        mock_disk_usage, 
        mock_virtual_memory, 
        mock_cpu_percent,
        monitoring_service
    ):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_cpu_percent.return_value = 45.2
        
        mock_memory = Mock()
        mock_memory.percent = 62.1
        mock_virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.used = 500 * 1024**3  # 500GB
        mock_disk.total = 1000 * 1024**3  # 1TB
        mock_disk_usage.return_value = mock_disk
        
        mock_network = Mock()
        mock_network.bytes_sent = 1024**3  # 1GB
        mock_network.bytes_recv = 2 * 1024**3  # 2GB
        mock_net_io.return_value = mock_network
        
        # Mock metric recording
        monitoring_service.record_metric = AsyncMock()
        
        # Collect metrics
        await monitoring_service.collect_system_metrics()
        
        # Assert metrics were recorded
        assert monitoring_service.record_metric.call_count >= 5  # CPU, memory, disk, network sent/recv
        
        # Check specific metric calls
        metric_calls = [call[1] for call in monitoring_service.record_metric.call_args_list]
        
        # Find CPU metric
        cpu_calls = [call for call in metric_calls if call.get("labels", {}).get("resource") == "cpu"]
        assert len(cpu_calls) == 1
        assert cpu_calls[0]["value"] == 45.2
        
        # Find memory metric
        memory_calls = [call for call in metric_calls if call.get("labels", {}).get("resource") == "memory"]
        assert len(memory_calls) == 1
        assert memory_calls[0]["value"] == 62.1


class TestAlertManagement:
    """Test alert management functionality."""

    @pytest.mark.asyncio
    async def test_create_alert_policy(self, monitoring_service):
        """Test creating an alert policy."""
        # Create alert policy
        policy_id = await monitoring_service.create_alert_policy(
            name="High CPU Usage",
            condition={"metric": "cpu_usage", "threshold": 80},
            notification_channels=["channel-1", "channel-2"],
            severity=AlertSeverity.WARNING
        )
        
        # Assert policy was created
        assert policy_id == "alert-policy-high-cpu-usage"

    @pytest.mark.asyncio
    async def test_create_alert_policy_error(self, monitoring_service):
        """Test alert policy creation error handling."""
        # This would test actual error scenarios
        # For now, just ensure the method exists and can be called
        try:
            await monitoring_service.create_alert_policy(
                name="Test Alert",
                condition={},
                notification_channels=[],
                severity=AlertSeverity.INFO
            )
        except MonitoringError:
            pass  # Expected for invalid configuration


class TestDashboardData:
    """Test dashboard data generation."""

    @pytest.mark.asyncio
    async def test_get_metrics_dashboard_data(self, monitoring_service):
        """Test getting dashboard metrics data."""
        # Mock dependencies
        monitoring_service.run_health_checks = AsyncMock(return_value={
            "overall_status": HealthStatus.HEALTHY,
            "checks": {}
        })
        monitoring_service._get_metric_value = AsyncMock(return_value=100.0)
        
        # Get dashboard data
        dashboard_data = await monitoring_service.get_metrics_dashboard_data(
            time_range=timedelta(hours=24)
        )
        
        # Assert structure
        assert "time_range" in dashboard_data
        assert "metrics" in dashboard_data
        assert "system_health" in dashboard_data
        
        # Assert time range
        assert "start" in dashboard_data["time_range"]
        assert "end" in dashboard_data["time_range"]
        
        # Assert metrics
        metrics = dashboard_data["metrics"]
        assert "request_count" in metrics
        assert "error_rate" in metrics
        assert "avg_processing_time" in metrics
        assert "active_users" in metrics

    @pytest.mark.asyncio
    async def test_get_metrics_dashboard_data_error(self, monitoring_service):
        """Test dashboard data error handling."""
        # Mock health checks to fail
        monitoring_service.run_health_checks = AsyncMock(side_effect=Exception("Health check failed"))
        
        # Should raise MonitoringError
        with pytest.raises(MonitoringError):
            await monitoring_service.get_metrics_dashboard_data()


class TestMonitoringLoop:
    """Test monitoring loop functionality."""

    @pytest.mark.asyncio
    async def test_start_monitoring_loop_single_iteration(self, monitoring_service):
        """Test a single iteration of the monitoring loop."""
        # Mock dependencies
        monitoring_service.collect_system_metrics = AsyncMock()
        monitoring_service.run_health_checks = AsyncMock(return_value={
            "overall_status": HealthStatus.HEALTHY
        })
        monitoring_service.report_error = AsyncMock()
        
        # Create a task that will run one iteration then cancel itself
        async def run_one_iteration():
            # Start the monitoring loop
            task = asyncio.create_task(monitoring_service.start_monitoring_loop(interval=0.1))
            
            # Wait a bit for one iteration
            await asyncio.sleep(0.2)
            
            # Cancel the task
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Run the test
        await run_one_iteration()
        
        # Assert methods were called
        monitoring_service.collect_system_metrics.assert_called()
        monitoring_service.run_health_checks.assert_called()

    @pytest.mark.asyncio
    async def test_monitoring_loop_error_handling(self, monitoring_service):
        """Test monitoring loop error handling."""
        # Mock system metrics to fail
        monitoring_service.collect_system_metrics = AsyncMock(side_effect=Exception("Metrics failed"))
        monitoring_service.run_health_checks = AsyncMock(return_value={
            "overall_status": HealthStatus.HEALTHY
        })
        monitoring_service.report_error = AsyncMock()
        
        # Create a task that will run briefly then cancel
        async def run_with_error():
            task = asyncio.create_task(monitoring_service.start_monitoring_loop(interval=0.1))
            
            # Wait for error to occur
            await asyncio.sleep(0.2)
            
            # Cancel the task
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Run the test
        await run_with_error()
        
        # Assert error was reported
        monitoring_service.report_error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])