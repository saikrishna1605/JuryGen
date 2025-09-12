"""
Error Reporting and Tracking System.

Provides comprehensive error reporting including:
- Automatic error detection and reporting
- Error categorization and severity assessment
- Integration with Cloud Error Reporting
- Error trend analysis and alerting
"""

import traceback
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

try:
    from google.cloud import error_reporting
    from google.cloud import logging
    ERROR_REPORTING_AVAILABLE = True
except ImportError:
    ERROR_REPORTING_AVAILABLE = False
    error_reporting = None
    logging = None

from ..core.config import get_settings

settings = get_settings()


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    PROCESSING = "processing"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorReport:
    """Error report data structure."""
    error_id: str
    timestamp: datetime
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    stack_trace: str
    context: Dict[str, Any]
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    resolved: bool = False


class ErrorReporter:
    """Handles error reporting and tracking."""
    
    def __init__(self):
        if ERROR_REPORTING_AVAILABLE:
            self.error_client = error_reporting.Client()
            self.logging_client = logging.Client()
            self.logger = self.logging_client.logger("ai-legal-companion-errors")
        else:
            self.error_client = None
            self.logging_client = None
            self.logger = None
        
        # Error tracking
        self._error_history: List[ErrorReport] = []
        self._error_patterns: Dict[str, int] = {}
    
    async def report_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> str:
        """Report an error with context."""
        # Generate error ID
        error_id = f"error_{datetime.utcnow().timestamp()}"
        
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        # Categorize error
        category = self._categorize_error(error, context)
        
        # Determine severity if not provided
        if severity is None:
            severity = self._assess_severity(error, category, context)
        
        # Create error report
        error_report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            message=str(error),
            category=category,
            severity=severity,
            stack_trace=stack_trace,
            context=context or {},
            user_id=user_id,
            request_id=request_id
        )
        
        # Store error report
        self._error_history.append(error_report)
        
        # Track error patterns
        error_pattern = f"{type(error).__name__}:{category.value}"
        self._error_patterns[error_pattern] = self._error_patterns.get(error_pattern, 0) + 1
        
        # Report to Cloud Error Reporting
        await self._report_to_cloud(error_report)
        
        # Log structured error
        await self._log_structured_error(error_report)
        
        # Record metrics
        await self._record_error_metrics(error_report)
        
        return error_id
    
    async def get_error_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_errors = [
            e for e in self._error_history
            if e.timestamp >= cutoff_time
        ]
        
        if not recent_errors:
            return {
                "period_hours": hours,
                "total_errors": 0,
                "error_rate": 0,
                "top_errors": [],
                "severity_breakdown": {}
            }
        
        # Calculate error metrics
        total_errors = len(recent_errors)
        
        # Group by category
        category_counts = {}
        for error in recent_errors:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
        
        # Group by severity
        severity_counts = {}
        for error in recent_errors:
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        # Top error patterns
        pattern_counts = {}
        for error in recent_errors:
            pattern = f"{error.category.value}:{error.message[:50]}"
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        top_errors = sorted(
            pattern_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "period_hours": hours,
            "total_errors": total_errors,
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "top_errors": [{"pattern": pattern, "count": count} for pattern, count in top_errors],
            "critical_errors": len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
        }
    
    def _categorize_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorCategory:
        """Categorize error based on type and context."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Authentication errors
        if any(keyword in error_message for keyword in ["auth", "token", "login", "unauthorized"]):
            return ErrorCategory.AUTHENTICATION
        
        # Authorization errors
        if any(keyword in error_message for keyword in ["permission", "forbidden", "access denied"]):
            return ErrorCategory.AUTHORIZATION
        
        # Validation errors
        if any(keyword in error_message for keyword in ["validation", "invalid", "required", "format"]):
            return ErrorCategory.VALIDATION
        
        # Database errors
        if any(keyword in error_message for keyword in ["firestore", "database", "collection", "document"]):
            return ErrorCategory.DATABASE
        
        # Storage errors
        if any(keyword in error_message for keyword in ["storage", "bucket", "upload", "download"]):
            return ErrorCategory.STORAGE
        
        # External API errors
        if any(keyword in error_message for keyword in ["api", "request", "response", "timeout", "connection"]):
            return ErrorCategory.EXTERNAL_API
        
        # Processing errors
        if any(keyword in error_message for keyword in ["processing", "analysis", "ocr", "ai", "model"]):
            return ErrorCategory.PROCESSING
        
        # Network errors
        if any(keyword in error_message for keyword in ["network", "socket", "dns", "ssl"]):
            return ErrorCategory.NETWORK
        
        # System errors
        if any(keyword in error_message for keyword in ["memory", "cpu", "disk", "system"]):
            return ErrorCategory.SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorSeverity:
        """Assess error severity."""
        error_message = str(error).lower()
        
        # Critical errors
        if any(keyword in error_message for keyword in ["critical", "fatal", "crash", "corruption"]):
            return ErrorSeverity.CRITICAL
        
        if category in [ErrorCategory.SYSTEM, ErrorCategory.DATABASE]:
            return ErrorSeverity.HIGH
        
        # High severity errors
        if any(keyword in error_message for keyword in ["security", "breach", "unauthorized access"]):
            return ErrorSeverity.CRITICAL
        
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.PROCESSING, ErrorCategory.EXTERNAL_API]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [ErrorCategory.VALIDATION]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    async def _report_to_cloud(self, error_report: ErrorReport):
        """Report error to Cloud Error Reporting."""
        try:
            self.error_client.report_exception(
                http_context={
                    "method": error_report.context.get("method", "UNKNOWN"),
                    "url": error_report.context.get("url", ""),
                    "userAgent": error_report.context.get("user_agent", ""),
                    "responseStatusCode": error_report.context.get("status_code", 500)
                },
                user=error_report.user_id or "anonymous"
            )
        except Exception as e:
            print(f"Failed to report error to Cloud Error Reporting: {e}")
    
    async def _log_structured_error(self, error_report: ErrorReport):
        """Log structured error data."""
        log_entry = {
            "error_id": error_report.error_id,
            "timestamp": error_report.timestamp.isoformat(),
            "message": error_report.message,
            "category": error_report.category.value,
            "severity": error_report.severity.value,
            "stack_trace": error_report.stack_trace,
            "context": error_report.context,
            "user_id": error_report.user_id,
            "request_id": error_report.request_id,
            "type": "error"
        }
        
        try:
            self.logger.log_struct(log_entry, severity=error_report.severity.value.upper())
        except Exception as e:
            print(f"Failed to log structured error: {e}")
    
    async def _record_error_metrics(self, error_report: ErrorReport):
        """Record error metrics to monitoring."""
        try:
            await monitoring_service.record_metric(
                metric_type="custom.googleapis.com/ai_legal_companion/error_rate",
                value=1,
                labels={
                    "error_type": error_report.category.value,
                    "service": "backend",
                    "severity": error_report.severity.value
                }
            )
        except Exception as e:
            print(f"Failed to record error metrics: {e}")


# Singleton instance
error_reporter = ErrorReporter() if ERROR_REPORTING_AVAILABLE else None