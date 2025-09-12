"""
Cloud Monitoring Alert Policies Configuration.

Creates and manages alert policies for system monitoring,
error tracking, and performance thresholds.
"""

from typing import Dict, List, Any, Optional, Union

try:
    from google.cloud import monitoring_v3
    from google.cloud.monitoring_v3 import types
    MONITORING_AVAILABLE = True
    AlertPolicyType = types.AlertPolicy
except ImportError:
    MONITORING_AVAILABLE = False
    monitoring_v3 = None
    types = None
    AlertPolicyType = Any

from ..core.config import get_settings

settings = get_settings()


class AlertManager:
    """Manages Cloud Monitoring alert policies."""
    
    def __init__(self):
        if MONITORING_AVAILABLE:
            self.client = monitoring_v3.AlertPolicyServiceClient()
            self.project_id = settings.GOOGLE_CLOUD_PROJECT
            self.project_name = f"projects/{self.project_id}"
        else:
            self.client = None
            self.project_id = None
            self.project_name = None
    
    def _check_monitoring_available(self):
        """Check if monitoring is available and return appropriate response."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        return None
    
    async def create_high_error_rate_alert(self, notification_channels: List[str]) -> str:
        """Create alert for high error rate."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        alert_policy = types.AlertPolicy(
            display_name="High Error Rate - AI Legal Companion",
            documentation=types.AlertPolicy.Documentation(
                content="Alert triggered when error rate exceeds 5% over 5 minutes",
                mime_type="text/markdown"
            ),
            conditions=[
                types.AlertPolicy.Condition(
                    display_name="Error rate > 5%",
                    condition_threshold=types.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/ai_legal_companion/error_rate"',
                        comparison=types.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=0.05,
                        duration={"seconds": 300},  # 5 minutes
                        aggregations=[
                            types.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=types.Aggregation.Aligner.ALIGN_MEAN,
                                cross_series_reducer=types.Aggregation.Reducer.REDUCE_MEAN
                            )
                        ]
                    )
                )
            ],
            combiner=types.AlertPolicy.ConditionCombinerType.AND,
            enabled=True,
            notification_channels=notification_channels,
            alert_strategy=types.AlertPolicy.AlertStrategy(
                auto_close={"seconds": 1800}  # Auto-close after 30 minutes
            )
        )
        
        response = self.client.create_alert_policy(
            parent=self.project_name,
            alert_policy=alert_policy
        )
        
        return response.name
    
    async def create_high_cpu_usage_alert(self, notification_channels: List[str]) -> str:
        """Create alert for high CPU usage."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        alert_policy = types.AlertPolicy(
            display_name="High CPU Usage - AI Legal Companion",
            documentation=types.AlertPolicy.Documentation(
                content="Alert triggered when CPU usage exceeds 80% for 10 minutes",
                mime_type="text/markdown"
            ),
            conditions=[
                types.AlertPolicy.Condition(
                    display_name="CPU usage > 80%",
                    condition_threshold=types.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/ai_legal_companion/cpu_usage"',
                        comparison=types.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=80.0,
                        duration={"seconds": 600},  # 10 minutes
                        aggregations=[
                            types.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=types.Aggregation.Aligner.ALIGN_MEAN
                            )
                        ]
                    )
                )
            ],
            combiner=types.AlertPolicy.ConditionCombinerType.AND,
            enabled=True,
            notification_channels=notification_channels
        )
        
        response = self.client.create_alert_policy(
            parent=self.project_name,
            alert_policy=alert_policy
        )
        
        return response.name
    
    async def create_high_memory_usage_alert(self, notification_channels: List[str]) -> str:
        """Create alert for high memory usage."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        alert_policy = types.AlertPolicy(
            display_name="High Memory Usage - AI Legal Companion",
            documentation=types.AlertPolicy.Documentation(
                content="Alert triggered when memory usage exceeds 85% for 5 minutes",
                mime_type="text/markdown"
            ),
            conditions=[
                types.AlertPolicy.Condition(
                    display_name="Memory usage > 85%",
                    condition_threshold=types.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/ai_legal_companion/memory_usage"',
                        comparison=types.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=85.0,
                        duration={"seconds": 300},  # 5 minutes
                        aggregations=[
                            types.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=types.Aggregation.Aligner.ALIGN_MEAN
                            )
                        ]
                    )
                )
            ],
            combiner=types.AlertPolicy.ConditionCombinerType.AND,
            enabled=True,
            notification_channels=notification_channels
        )
        
        response = self.client.create_alert_policy(
            parent=self.project_name,
            alert_policy=alert_policy
        )
        
        return response.name
    
    async def create_slow_processing_alert(self, notification_channels: List[str]) -> str:
        """Create alert for slow document processing."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        alert_policy = types.AlertPolicy(
            display_name="Slow Document Processing - AI Legal Companion",
            documentation=types.AlertPolicy.Documentation(
                content="Alert triggered when document processing takes longer than 5 minutes on average",
                mime_type="text/markdown"
            ),
            conditions=[
                types.AlertPolicy.Condition(
                    display_name="Processing duration > 300s",
                    condition_threshold=types.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/ai_legal_companion/document_processing_duration"',
                        comparison=types.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=300.0,  # 5 minutes
                        duration={"seconds": 600},  # 10 minutes
                        aggregations=[
                            types.Aggregation(
                                alignment_period={"seconds": 300},
                                per_series_aligner=types.Aggregation.Aligner.ALIGN_MEAN,
                                cross_series_reducer=types.Aggregation.Reducer.REDUCE_PERCENTILE_95
                            )
                        ]
                    )
                )
            ],
            combiner=types.AlertPolicy.ConditionCombinerType.AND,
            enabled=True,
            notification_channels=notification_channels
        )
        
        response = self.client.create_alert_policy(
            parent=self.project_name,
            alert_policy=alert_policy
        )
        
        return response.name
    
    async def create_system_health_alert(self, notification_channels: List[str]) -> str:
        """Create alert for system health degradation."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        alert_policy = types.AlertPolicy(
            display_name="System Health Degraded - AI Legal Companion",
            documentation=types.AlertPolicy.Documentation(
                content="Alert triggered when system health status is not healthy",
                mime_type="text/markdown"
            ),
            conditions=[
                types.AlertPolicy.Condition(
                    display_name="System health < 1",
                    condition_threshold=types.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/ai_legal_companion/health_status"',
                        comparison=types.ComparisonType.COMPARISON_LESS_THAN,
                        threshold_value=1.0,
                        duration={"seconds": 60},  # 1 minute
                        aggregations=[
                            types.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=types.Aggregation.Aligner.ALIGN_MEAN
                            )
                        ]
                    )
                )
            ],
            combiner=types.AlertPolicy.ConditionCombinerType.AND,
            enabled=True,
            notification_channels=notification_channels
        )
        
        response = self.client.create_alert_policy(
            parent=self.project_name,
            alert_policy=alert_policy
        )
        
        return response.name
    
    async def create_ai_model_latency_alert(self, notification_channels: List[str]) -> str:
        """Create alert for high AI model latency."""
        if not MONITORING_AVAILABLE:
            return "monitoring-disabled"
        alert_policy = types.AlertPolicy(
            display_name="High AI Model Latency - AI Legal Companion",
            documentation=types.AlertPolicy.Documentation(
                content="Alert triggered when AI model latency exceeds 5 seconds",
                mime_type="text/markdown"
            ),
            conditions=[
                types.AlertPolicy.Condition(
                    display_name="AI model latency > 5000ms",
                    condition_threshold=types.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/ai_legal_companion/ai_model_latency"',
                        comparison=types.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=5000.0,  # 5 seconds
                        duration={"seconds": 300},  # 5 minutes
                        aggregations=[
                            types.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=types.Aggregation.Aligner.ALIGN_MEAN,
                                cross_series_reducer=types.Aggregation.Reducer.REDUCE_PERCENTILE_95
                            )
                        ]
                    )
                )
            ],
            combiner=types.AlertPolicy.ConditionCombinerType.AND,
            enabled=True,
            notification_channels=notification_channels
        )
        
        response = self.client.create_alert_policy(
            parent=self.project_name,
            alert_policy=alert_policy
        )
        
        return response.name
    
    async def create_notification_channel(
        self,
        display_name: str,
        channel_type: str,
        config: Dict[str, str]
    ) -> str:
        """Create a notification channel."""
        notification_channel = types.NotificationChannel(
            display_name=display_name,
            type=channel_type,
            labels=config,
            enabled=True
        )
        
        response = self.client.create_notification_channel(
            parent=self.project_name,
            notification_channel=notification_channel
        )
        
        return response.name
    
    async def setup_email_notification_channel(self, email: str) -> str:
        """Set up email notification channel."""
        return await self.create_notification_channel(
            display_name=f"Email - {email}",
            channel_type="email",
            config={"email_address": email}
        )
    
    async def setup_slack_notification_channel(self, webhook_url: str) -> str:
        """Set up Slack notification channel."""
        return await self.create_notification_channel(
            display_name="Slack Notifications",
            channel_type="slack",
            config={"url": webhook_url}
        )
    
    async def setup_all_alerts(
        self,
        notification_channels: List[str]
    ) -> Dict[str, str]:
        """Set up all monitoring alerts."""
        if not MONITORING_AVAILABLE:
            return {"status": "monitoring-disabled"}
        alerts = {}
        
        try:
            alerts["high_error_rate"] = await self.create_high_error_rate_alert(notification_channels)
            alerts["high_cpu_usage"] = await self.create_high_cpu_usage_alert(notification_channels)
            alerts["high_memory_usage"] = await self.create_high_memory_usage_alert(notification_channels)
            alerts["slow_processing"] = await self.create_slow_processing_alert(notification_channels)
            alerts["system_health"] = await self.create_system_health_alert(notification_channels)
            alerts["ai_model_latency"] = await self.create_ai_model_latency_alert(notification_channels)
            
            return alerts
            
        except Exception as e:
            raise Exception(f"Failed to create alert policies: {e}")
    
    async def list_alert_policies(self) -> List[AlertPolicyType]:
        """List all alert policies."""
        if not MONITORING_AVAILABLE:
            return []
        policies = []
        
        for policy in self.client.list_alert_policies(parent=self.project_name):
            policies.append(policy)
        
        return policies
    
    async def delete_alert_policy(self, policy_name: str):
        """Delete an alert policy."""
        if not MONITORING_AVAILABLE:
            return
        self.client.delete_alert_policy(name=policy_name)


# Singleton instance
alert_manager = AlertManager() if MONITORING_AVAILABLE else None