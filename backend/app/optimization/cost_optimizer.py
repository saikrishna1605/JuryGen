"""
Cost Optimization Service for AI Legal Companion.

Implements intelligent cost optimization strategies including:
- AI model selection based on task complexity
- Caching strategies for embeddings and analysis results
- Resource usage monitoring and optimization
- Cost tracking and budgeting
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from google.cloud import monitoring_v3
from google.cloud import billing_v1
from google.cloud import aiplatform

from ..core.config import get_settings
from ..services.monitoring import monitoring_service

settings = get_settings()


class ModelTier(Enum):
    """AI model tiers based on cost and capability."""
    FLASH = "gemini-1.5-flash"  # Fast, cost-effective
    PRO = "gemini-1.5-pro"      # High capability, higher cost
    ULTRA = "gemini-ultra"      # Maximum capability, highest cost


class TaskComplexity(Enum):
    """Task complexity levels for model selection."""
    LOW = "low"        # Simple tasks (basic OCR, simple Q&A)
    MEDIUM = "medium"  # Standard tasks (clause analysis, summarization)
    HIGH = "high"      # Complex tasks (legal reasoning, complex analysis)


@dataclass
class CostMetrics:
    """Cost metrics data structure."""
    total_cost: float
    ai_model_cost: float
    storage_cost: float
    compute_cost: float
    network_cost: float
    period_start: datetime
    period_end: datetime


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    category: str
    description: str
    potential_savings: float
    implementation_effort: str
    priority: str


class CostOptimizer:
    """Manages cost optimization strategies."""
    
    def __init__(self):
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.billing_client = billing_v1.CloudBillingClient()
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        
        # Cost tracking
        self._cost_cache = {}
        self._usage_patterns = {}
        
        # Model selection rules
        self._model_selection_rules = {
            TaskComplexity.LOW: ModelTier.FLASH,
            TaskComplexity.MEDIUM: ModelTier.FLASH,  # Start with Flash, upgrade if needed
            TaskComplexity.HIGH: ModelTier.PRO,
        }
        
        # Cost thresholds (USD)
        self._daily_budget = float(settings.DAILY_COST_BUDGET or 100.0)
        self._monthly_budget = float(settings.MONTHLY_COST_BUDGET or 3000.0)
    
    async def select_optimal_model(
        self,
        task_type: str,
        document_size: int,
        complexity_hints: Optional[Dict[str, Any]] = None
    ) -> Tuple[ModelTier, str]:
        """
        Select the optimal AI model based on task requirements and cost.
        
        Args:
            task_type: Type of task (ocr, analysis, summarization, etc.)
            document_size: Size of document in bytes
            complexity_hints: Additional complexity indicators
            
        Returns:
            Tuple of (selected_model_tier, reasoning)
        """
        # Determine task complexity
        complexity = await self._assess_task_complexity(
            task_type, document_size, complexity_hints
        )
        
        # Check current cost usage
        current_costs = await self.get_current_period_costs()
        daily_usage_ratio = current_costs.total_cost / self._daily_budget
        
        # Apply cost-based adjustments
        selected_tier = self._model_selection_rules[complexity]
        reasoning = f"Base selection for {complexity.value} complexity task"
        
        # Downgrade if approaching budget limits
        if daily_usage_ratio > 0.8:  # 80% of daily budget used
            if selected_tier == ModelTier.PRO:
                selected_tier = ModelTier.FLASH
                reasoning += " (downgraded to Flash due to budget constraints)"
            elif selected_tier == ModelTier.ULTRA:
                selected_tier = ModelTier.PRO
                reasoning += " (downgraded to Pro due to budget constraints)"
        
        # Upgrade for critical tasks if budget allows
        if (task_type == "legal_analysis" and 
            daily_usage_ratio < 0.5 and 
            selected_tier == ModelTier.FLASH):
            selected_tier = ModelTier.PRO
            reasoning += " (upgraded to Pro for critical legal analysis)"
        
        return selected_tier, reasoning
    
    async def _assess_task_complexity(
        self,
        task_type: str,
        document_size: int,
        complexity_hints: Optional[Dict[str, Any]] = None
    ) -> TaskComplexity:
        """Assess task complexity based on various factors."""
        complexity_score = 0
        
        # Base complexity by task type
        task_complexity_map = {
            "ocr": 1,
            "basic_qa": 1,
            "clause_extraction": 2,
            "summarization": 2,
            "risk_assessment": 3,
            "legal_analysis": 3,
            "contract_comparison": 4,
            "legal_reasoning": 4,
        }
        
        complexity_score += task_complexity_map.get(task_type, 2)
        
        # Document size factor
        if document_size > 10 * 1024 * 1024:  # > 10MB
            complexity_score += 2
        elif document_size > 1 * 1024 * 1024:  # > 1MB
            complexity_score += 1
        
        # Additional complexity hints
        if complexity_hints:
            if complexity_hints.get("multi_language", False):
                complexity_score += 1
            if complexity_hints.get("technical_content", False):
                complexity_score += 1
            if complexity_hints.get("legal_jurisdiction_specific", False):
                complexity_score += 1
        
        # Map score to complexity level
        if complexity_score <= 2:
            return TaskComplexity.LOW
        elif complexity_score <= 4:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.HIGH
    
    async def get_current_period_costs(self) -> CostMetrics:
        """Get current period cost metrics."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=1)  # Last 24 hours
        
        # Check cache first
        cache_key = f"costs_{start_time.date()}"
        if cache_key in self._cost_cache:
            cached_data, cache_time = self._cost_cache[cache_key]
            if datetime.utcnow() - cache_time < timedelta(hours=1):
                return cached_data
        
        try:
            # Get billing data from Google Cloud Billing API
            # This is a simplified implementation
            total_cost = await self._get_billing_data(start_time, end_time)
            
            # Break down costs by category
            ai_model_cost = total_cost * 0.6  # Estimated 60% for AI models
            storage_cost = total_cost * 0.15   # Estimated 15% for storage
            compute_cost = total_cost * 0.20   # Estimated 20% for compute
            network_cost = total_cost * 0.05   # Estimated 5% for network
            
            cost_metrics = CostMetrics(
                total_cost=total_cost,
                ai_model_cost=ai_model_cost,
                storage_cost=storage_cost,
                compute_cost=compute_cost,
                network_cost=network_cost,
                period_start=start_time,
                period_end=end_time
            )
            
            # Cache the result
            self._cost_cache[cache_key] = (cost_metrics, datetime.utcnow())
            
            return cost_metrics
            
        except Exception as e:
            # Return default metrics if billing API fails
            return CostMetrics(
                total_cost=0.0,
                ai_model_cost=0.0,
                storage_cost=0.0,
                compute_cost=0.0,
                network_cost=0.0,
                period_start=start_time,
                period_end=end_time
            )
    
    async def _get_billing_data(self, start_time: datetime, end_time: datetime) -> float:
        """Get billing data from Google Cloud Billing API."""
        try:
            # This would integrate with the actual Billing API
            # For now, return a simulated cost based on usage metrics
            
            # Get usage metrics from monitoring
            request_count = await self._get_metric_value(
                "custom.googleapis.com/ai_legal_companion/api_request_count",
                start_time, end_time
            )
            
            # Estimate cost based on request count
            # Rough estimate: $0.01 per request (including all services)
            estimated_cost = request_count * 0.01
            
            return min(estimated_cost, self._daily_budget)  # Cap at daily budget
            
        except Exception:
            return 0.0
    
    async def _get_metric_value(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Get metric value from Cloud Monitoring."""
        try:
            # This would query actual metrics
            # For now, return a simulated value
            return 100.0  # Simulated request count
        except Exception:
            return 0.0
    
    async def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Get current costs and usage patterns
        current_costs = await self.get_current_period_costs()
        usage_patterns = await self._analyze_usage_patterns()
        
        # AI Model optimization
        if current_costs.ai_model_cost > current_costs.total_cost * 0.7:
            recommendations.append(OptimizationRecommendation(
                category="AI Models",
                description="High AI model costs detected. Consider using Gemini Flash for simpler tasks.",
                potential_savings=current_costs.ai_model_cost * 0.3,
                implementation_effort="Low",
                priority="High"
            ))
        
        # Caching optimization
        cache_hit_rate = usage_patterns.get("cache_hit_rate", 0.0)
        if cache_hit_rate < 0.6:  # Less than 60% cache hit rate
            recommendations.append(OptimizationRecommendation(
                category="Caching",
                description="Low cache hit rate. Implement more aggressive caching for embeddings and analysis results.",
                potential_savings=current_costs.ai_model_cost * 0.2,
                implementation_effort="Medium",
                priority="Medium"
            ))
        
        # Storage optimization
        if current_costs.storage_cost > current_costs.total_cost * 0.2:
            recommendations.append(OptimizationRecommendation(
                category="Storage",
                description="High storage costs. Implement lifecycle policies and compress old documents.",
                potential_savings=current_costs.storage_cost * 0.4,
                implementation_effort="Low",
                priority="Medium"
            ))
        
        # Compute optimization
        avg_cpu_usage = usage_patterns.get("avg_cpu_usage", 50.0)
        if avg_cpu_usage < 30.0:  # Low CPU utilization
            recommendations.append(OptimizationRecommendation(
                category="Compute",
                description="Low CPU utilization detected. Consider reducing instance sizes or implementing auto-scaling.",
                potential_savings=current_costs.compute_cost * 0.25,
                implementation_effort="Medium",
                priority="Low"
            ))
        
        # Batch processing optimization
        if usage_patterns.get("peak_hour_ratio", 1.0) > 2.0:
            recommendations.append(OptimizationRecommendation(
                category="Batch Processing",
                description="High peak-hour usage. Consider batch processing during off-peak hours.",
                potential_savings=current_costs.total_cost * 0.15,
                implementation_effort="High",
                priority="Medium"
            ))
        
        return recommendations
    
    async def _analyze_usage_patterns(self) -> Dict[str, float]:
        """Analyze usage patterns for optimization insights."""
        # This would analyze actual usage data
        # For now, return simulated patterns
        return {
            "cache_hit_rate": 0.45,  # 45% cache hit rate
            "avg_cpu_usage": 35.0,   # 35% average CPU usage
            "peak_hour_ratio": 2.5,  # 2.5x higher usage during peak hours
            "avg_request_size": 1024 * 1024,  # 1MB average request size
        }
    
    async def implement_caching_strategy(self) -> Dict[str, Any]:
        """Implement intelligent caching strategy."""
        caching_config = {
            "embeddings": {
                "ttl": 86400 * 7,  # 7 days for embeddings
                "max_size": "1GB",
                "eviction_policy": "LRU"
            },
            "analysis_results": {
                "ttl": 86400 * 30,  # 30 days for analysis results
                "max_size": "2GB",
                "eviction_policy": "LRU"
            },
            "ocr_results": {
                "ttl": 86400 * 90,  # 90 days for OCR results
                "max_size": "5GB",
                "eviction_policy": "LRU"
            },
            "api_responses": {
                "ttl": 3600,  # 1 hour for API responses
                "max_size": "500MB",
                "eviction_policy": "TTL"
            }
        }
        
        # Implement cache warming for frequently accessed data
        await self._warm_cache()
        
        return caching_config
    
    async def _warm_cache(self):
        """Warm cache with frequently accessed data."""
        # This would pre-load frequently accessed embeddings and results
        pass
    
    async def optimize_model_usage(self) -> Dict[str, Any]:
        """Optimize AI model usage patterns."""
        optimization_config = {
            "model_selection": {
                "use_flash_for_simple_tasks": True,
                "upgrade_threshold": 0.8,  # Upgrade to Pro if Flash confidence < 80%
                "batch_similar_requests": True,
                "max_batch_size": 10
            },
            "request_optimization": {
                "compress_inputs": True,
                "truncate_long_documents": True,
                "max_input_tokens": 100000,
                "use_streaming": True
            },
            "response_optimization": {
                "cache_embeddings": True,
                "reuse_similar_analyses": True,
                "similarity_threshold": 0.9
            }
        }
        
        return optimization_config
    
    async def monitor_cost_budgets(self) -> Dict[str, Any]:
        """Monitor cost budgets and send alerts."""
        current_costs = await self.get_current_period_costs()
        
        # Daily budget monitoring
        daily_usage_ratio = current_costs.total_cost / self._daily_budget
        daily_status = "normal"
        
        if daily_usage_ratio > 0.9:
            daily_status = "critical"
            await self._send_budget_alert("daily", daily_usage_ratio)
        elif daily_usage_ratio > 0.7:
            daily_status = "warning"
            await self._send_budget_alert("daily", daily_usage_ratio)
        
        # Monthly budget projection
        days_in_month = 30
        current_day = datetime.utcnow().day
        projected_monthly_cost = (current_costs.total_cost / current_day) * days_in_month
        monthly_usage_ratio = projected_monthly_cost / self._monthly_budget
        monthly_status = "normal"
        
        if monthly_usage_ratio > 0.9:
            monthly_status = "critical"
            await self._send_budget_alert("monthly", monthly_usage_ratio)
        elif monthly_usage_ratio > 0.7:
            monthly_status = "warning"
            await self._send_budget_alert("monthly", monthly_usage_ratio)
        
        return {
            "daily": {
                "budget": self._daily_budget,
                "current_cost": current_costs.total_cost,
                "usage_ratio": daily_usage_ratio,
                "status": daily_status
            },
            "monthly": {
                "budget": self._monthly_budget,
                "projected_cost": projected_monthly_cost,
                "usage_ratio": monthly_usage_ratio,
                "status": monthly_status
            }
        }
    
    async def _send_budget_alert(self, period: str, usage_ratio: float):
        """Send budget alert notification."""
        alert_message = f"Cost budget alert: {period} usage at {usage_ratio:.1%}"
        
        # Record alert metric
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/budget_alert",
            value=usage_ratio,
            labels={"period": period, "severity": "warning" if usage_ratio < 0.9 else "critical"}
        )
        
        # This would send actual notifications (email, Slack, etc.)
        print(f"BUDGET ALERT: {alert_message}")
    
    async def generate_cost_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive cost report."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get cost data for the period
        total_costs = 0.0
        daily_costs = []
        
        for i in range(days):
            day_start = start_time + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # This would get actual daily costs
            daily_cost = await self._get_billing_data(day_start, day_end)
            daily_costs.append({
                "date": day_start.date().isoformat(),
                "cost": daily_cost
            })
            total_costs += daily_cost
        
        # Get optimization recommendations
        recommendations = await self.get_optimization_recommendations()
        
        # Calculate potential savings
        total_potential_savings = sum(rec.potential_savings for rec in recommendations)
        
        return {
            "period": {
                "start_date": start_time.date().isoformat(),
                "end_date": end_time.date().isoformat(),
                "days": days
            },
            "costs": {
                "total": total_costs,
                "average_daily": total_costs / days,
                "daily_breakdown": daily_costs
            },
            "optimization": {
                "recommendations": [
                    {
                        "category": rec.category,
                        "description": rec.description,
                        "potential_savings": rec.potential_savings,
                        "implementation_effort": rec.implementation_effort,
                        "priority": rec.priority
                    }
                    for rec in recommendations
                ],
                "total_potential_savings": total_potential_savings,
                "savings_percentage": (total_potential_savings / total_costs * 100) if total_costs > 0 else 0
            },
            "budget_status": await self.monitor_cost_budgets()
        }


# Singleton instance
cost_optimizer = CostOptimizer()