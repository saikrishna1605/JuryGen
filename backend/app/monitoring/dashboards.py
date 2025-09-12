"""
Cloud Monitoring Dashboard Configuration.

Creates and manages Cloud Monitoring dashboards for system health,
performance metrics, and application observability.
"""

import json
from typing import Dict, List, Any

try:
    from google.cloud import monitoring_dashboard_v1
    from google.cloud.monitoring_dashboard_v1 import types
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    monitoring_dashboard_v1 = None
    types = None

from ..core.config import get_settings

settings = get_settings()


class DashboardManager:
    """Manages Cloud Monitoring dashboards."""
    
    def __init__(self):
        if DASHBOARD_AVAILABLE:
            self.client = monitoring_dashboard_v1.DashboardsServiceClient()
            self.project_id = settings.GOOGLE_CLOUD_PROJECT
            self.project_name = f"projects/{self.project_id}"
        else:
            self.client = None
            self.project_id = None
            self.project_name = None
    
    async def create_system_health_dashboard(self) -> str:
        """Create system health monitoring dashboard."""
        dashboard_config = {
            "displayName": "AI Legal Companion - System Health",
            "mosaicLayout": {
                "tiles": [
                    {
                        "width": 6,
                        "height": 4,
                        "widget": {
                            "title": "Overall System Health",
                            "scorecard": {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/health_status"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_MEAN"
                                        }
                                    }
                                },
                                "sparkChartView": {
                                    "sparkChartType": "SPARK_LINE"
                                }
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "xPos": 6,
                        "widget": {
                            "title": "API Request Rate",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/api_request_count"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_RATE"
                                            }
                                        }
                                    },
                                    "plotType": "LINE"
                                }],
                                "timeshiftDuration": "0s",
                                "yAxis": {
                                    "label": "Requests/sec",
                                    "scale": "LINEAR"
                                }
                            }
                        }
                    },
                    {
                        "width": 12,
                        "height": 4,
                        "yPos": 4,
                        "widget": {
                            "title": "Error Rate",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/error_rate"',
                                            "aggregation": {
                                                "alignmentPeriod": "300s",
                                                "perSeriesAligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plotType": "LINE"
                                }],
                                "yAxis": {
                                    "label": "Error Rate",
                                    "scale": "LINEAR"
                                },
                                "thresholds": [{
                                    "value": 0.05,
                                    "color": "YELLOW",
                                    "direction": "ABOVE"
                                }, {
                                    "value": 0.10,
                                    "color": "RED",
                                    "direction": "ABOVE"
                                }]
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "yPos": 8,
                        "widget": {
                            "title": "CPU Usage",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/cpu_usage"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plotType": "LINE"
                                }],
                                "yAxis": {
                                    "label": "CPU %",
                                    "scale": "LINEAR"
                                },
                                "thresholds": [{
                                    "value": 80,
                                    "color": "YELLOW",
                                    "direction": "ABOVE"
                                }, {
                                    "value": 90,
                                    "color": "RED",
                                    "direction": "ABOVE"
                                }]
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "xPos": 6,
                        "yPos": 8,
                        "widget": {
                            "title": "Memory Usage",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/memory_usage"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plotType": "LINE"
                                }],
                                "yAxis": {
                                    "label": "Memory %",
                                    "scale": "LINEAR"
                                },
                                "thresholds": [{
                                    "value": 80,
                                    "color": "YELLOW",
                                    "direction": "ABOVE"
                                }, {
                                    "value": 90,
                                    "color": "RED",
                                    "direction": "ABOVE"
                                }]
                            }
                        }
                    }
                ]
            }
        }
        
        dashboard = types.Dashboard(dashboard_config)
        
        response = self.client.create_dashboard(
            parent=self.project_name,
            dashboard=dashboard
        )
        
        return response.name
    
    async def create_performance_dashboard(self) -> str:
        """Create performance monitoring dashboard."""
        dashboard_config = {
            "displayName": "AI Legal Companion - Performance",
            "mosaicLayout": {
                "tiles": [
                    {
                        "width": 12,
                        "height": 4,
                        "widget": {
                            "title": "Document Processing Duration",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/document_processing_duration"',
                                            "aggregation": {
                                                "alignmentPeriod": "300s",
                                                "perSeriesAligner": "ALIGN_MEAN",
                                                "crossSeriesReducer": "REDUCE_PERCENTILE_95"
                                            }
                                        }
                                    },
                                    "plotType": "LINE"
                                }],
                                "yAxis": {
                                    "label": "Duration (seconds)",
                                    "scale": "LINEAR"
                                }
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "yPos": 4,
                        "widget": {
                            "title": "AI Model Latency",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/ai_model_latency"',
                                            "aggregation": {
                                                "alignmentPeriod": "300s",
                                                "perSeriesAligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plotType": "LINE"
                                }],
                                "yAxis": {
                                    "label": "Latency (ms)",
                                    "scale": "LINEAR"
                                }
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "xPos": 6,
                        "yPos": 4,
                        "widget": {
                            "title": "Active Users",
                            "scorecard": {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/active_users"',
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_MEAN"
                                        }
                                    }
                                },
                                "sparkChartView": {
                                    "sparkChartType": "SPARK_LINE"
                                }
                            }
                        }
                    },
                    {
                        "width": 12,
                        "height": 4,
                        "yPos": 8,
                        "widget": {
                            "title": "Storage Usage",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/storage_usage"',
                                            "aggregation": {
                                                "alignmentPeriod": "3600s",
                                                "perSeriesAligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plotType": "STACKED_AREA"
                                }],
                                "yAxis": {
                                    "label": "Storage (GB)",
                                    "scale": "LINEAR"
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        dashboard = types.Dashboard(dashboard_config)
        
        response = self.client.create_dashboard(
            parent=self.project_name,
            dashboard=dashboard
        )
        
        return response.name
    
    async def create_error_tracking_dashboard(self) -> str:
        """Create error tracking dashboard."""
        dashboard_config = {
            "displayName": "AI Legal Companion - Error Tracking",
            "mosaicLayout": {
                "tiles": [
                    {
                        "width": 12,
                        "height": 4,
                        "widget": {
                            "title": "Error Rate by Type",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/error_rate"',
                                            "aggregation": {
                                                "alignmentPeriod": "300s",
                                                "perSeriesAligner": "ALIGN_RATE",
                                                "crossSeriesReducer": "REDUCE_SUM",
                                                "groupByFields": ["metric.label.error_type"]
                                            }
                                        }
                                    },
                                    "plotType": "STACKED_AREA"
                                }],
                                "yAxis": {
                                    "label": "Errors/sec",
                                    "scale": "LINEAR"
                                }
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "yPos": 4,
                        "widget": {
                            "title": "Top Error Types",
                            "pieChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/error_rate"',
                                            "aggregation": {
                                                "alignmentPeriod": "3600s",
                                                "perSeriesAligner": "ALIGN_SUM",
                                                "crossSeriesReducer": "REDUCE_SUM",
                                                "groupByFields": ["metric.label.error_type"]
                                            }
                                        }
                                    }
                                }]
                            }
                        }
                    },
                    {
                        "width": 6,
                        "height": 4,
                        "xPos": 6,
                        "yPos": 4,
                        "widget": {
                            "title": "Error Count (24h)",
                            "scorecard": {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'metric.type="custom.googleapis.com/ai_legal_companion/error_rate"',
                                        "aggregation": {
                                            "alignmentPeriod": "86400s",
                                            "perSeriesAligner": "ALIGN_SUM"
                                        }
                                    }
                                },
                                "sparkChartView": {
                                    "sparkChartType": "SPARK_BAR"
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        dashboard = types.Dashboard(dashboard_config)
        
        response = self.client.create_dashboard(
            parent=self.project_name,
            dashboard=dashboard
        )
        
        return response.name
    
    async def setup_all_dashboards(self) -> Dict[str, str]:
        """Set up all monitoring dashboards."""
        dashboards = {}
        
        try:
            dashboards["system_health"] = await self.create_system_health_dashboard()
            dashboards["performance"] = await self.create_performance_dashboard()
            dashboards["error_tracking"] = await self.create_error_tracking_dashboard()
            
            return dashboards
            
        except Exception as e:
            raise Exception(f"Failed to create dashboards: {e}")


# Singleton instance
dashboard_manager = DashboardManager() if DASHBOARD_AVAILABLE else None