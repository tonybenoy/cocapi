"""
Request metrics tracking for cocapi
"""

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .config import RequestMetric
from .utils import format_endpoint_for_metrics


class MetricsTracker:
    """Tracks API request metrics and statistics"""

    def __init__(self, max_metrics: int = 1000):
        """
        Initialize metrics tracker

        Args:
            max_metrics: Maximum number of metrics to store (oldest are removed)
        """
        self.max_metrics = max_metrics
        self.metrics: List[RequestMetric] = []
        self._enabled = False

    def enable(self) -> None:
        """Enable metrics tracking"""
        self._enabled = True

    def disable(self) -> None:
        """Disable metrics tracking"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if metrics tracking is enabled"""
        return self._enabled

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        cache_hit: bool,
        error_type: Optional[str] = None,
    ) -> None:
        """Record metrics for a request if metrics are enabled"""
        if not self._enabled:
            return

        # Format endpoint for better grouping
        formatted_endpoint = format_endpoint_for_metrics(endpoint)

        metric = RequestMetric(
            endpoint=formatted_endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            timestamp=time.time(),
            cache_hit=cache_hit,
            error_type=error_type,
        )

        self.metrics.append(metric)

        # Keep only the most recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics :]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        if not self.metrics:
            return {"total_requests": 0, "message": "No metrics available"}

        total_requests = len(self.metrics)

        # Calculate success rate
        successful_requests = sum(1 for m in self.metrics if 200 <= m.status_code < 300)
        success_rate = (successful_requests / total_requests) * 100

        # Calculate cache hit rate
        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        cache_hit_rate = (cache_hits / total_requests) * 100

        # Calculate average response time
        avg_response_time = sum(m.response_time for m in self.metrics) / total_requests

        # Most used endpoints
        endpoint_counts: Dict[str, int] = defaultdict(int)
        for metric in self.metrics:
            endpoint_counts[metric.endpoint] += 1

        most_used_endpoints = sorted(
            endpoint_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Error breakdown
        error_counts: Dict[str, int] = defaultdict(int)
        for metric in self.metrics:
            if metric.error_type:
                error_counts[metric.error_type] += 1

        # Status code breakdown
        status_counts: Dict[int, int] = defaultdict(int)
        for metric in self.metrics:
            status_counts[metric.status_code] += 1

        # Response time percentiles
        response_times = sorted(m.response_time for m in self.metrics)
        percentiles = self._calculate_percentiles(response_times)

        return {
            "total_requests": total_requests,
            "success_rate": round(success_rate, 2),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_response_time": round(avg_response_time, 3),
            "response_time_percentiles": percentiles,
            "most_used_endpoints": most_used_endpoints,
            "status_code_breakdown": dict(status_counts),
            "error_breakdown": dict(error_counts),
            "timespan": {
                "start": min(m.timestamp for m in self.metrics),
                "end": max(m.timestamp for m in self.metrics),
                "duration_seconds": max(m.timestamp for m in self.metrics)
                - min(m.timestamp for m in self.metrics),
            },
        }

    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get metrics for a specific endpoint"""
        formatted_endpoint = format_endpoint_for_metrics(endpoint)
        endpoint_metrics = [m for m in self.metrics if m.endpoint == formatted_endpoint]

        if not endpoint_metrics:
            return {
                "endpoint": endpoint,
                "total_requests": 0,
                "message": "No metrics available for this endpoint",
            }

        total_requests = len(endpoint_metrics)
        successful_requests = sum(
            1 for m in endpoint_metrics if 200 <= m.status_code < 300
        )
        success_rate = (successful_requests / total_requests) * 100

        cache_hits = sum(1 for m in endpoint_metrics if m.cache_hit)
        cache_hit_rate = (cache_hits / total_requests) * 100

        avg_response_time = (
            sum(m.response_time for m in endpoint_metrics) / total_requests
        )

        response_times = sorted(m.response_time for m in endpoint_metrics)
        percentiles = self._calculate_percentiles(response_times)

        return {
            "endpoint": endpoint,
            "formatted_endpoint": formatted_endpoint,
            "total_requests": total_requests,
            "success_rate": round(success_rate, 2),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_response_time": round(avg_response_time, 3),
            "response_time_percentiles": percentiles,
        }

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error requests"""
        error_metrics = [
            m for m in self.metrics if m.status_code >= 400 or m.error_type
        ]

        # Sort by timestamp, most recent first
        error_metrics.sort(key=lambda x: x.timestamp, reverse=True)

        return [
            {
                "endpoint": m.endpoint,
                "method": m.method,
                "status_code": m.status_code,
                "error_type": m.error_type,
                "response_time": m.response_time,
                "timestamp": m.timestamp,
            }
            for m in error_metrics[:limit]
        ]

    def clear_metrics(self) -> None:
        """Clear all stored metrics"""
        self.metrics.clear()

    def _calculate_percentiles(self, sorted_values: List[float]) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not sorted_values:
            return {}

        def percentile(values: List[float], p: float) -> float:
            if not values:
                return 0.0
            k = (len(values) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(values):
                return values[f] * (1 - c) + values[f + 1] * c
            return values[f]

        return {
            "p50": round(percentile(sorted_values, 0.5), 3),
            "p75": round(percentile(sorted_values, 0.75), 3),
            "p90": round(percentile(sorted_values, 0.9), 3),
            "p95": round(percentile(sorted_values, 0.95), 3),
            "p99": round(percentile(sorted_values, 0.99), 3),
            "min": round(min(sorted_values), 3),
            "max": round(max(sorted_values), 3),
        }

    def export_metrics_csv(self) -> str:
        """Export metrics as CSV string"""
        if not self.metrics:
            return "No metrics to export"

        lines = [
            "endpoint,method,status_code,response_time,timestamp,cache_hit,error_type"
        ]

        for metric in self.metrics:
            lines.append(
                f"{metric.endpoint},{metric.method},{metric.status_code},"
                f"{metric.response_time},{metric.timestamp},{metric.cache_hit},"
                f"{metric.error_type or ''}"
            )

        return "\n".join(lines)

    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        if not self.metrics:
            return {"message": "No metrics available for insights"}

        insights = []
        summary = self.get_metrics_summary()

        # Check cache hit rate
        if summary["cache_hit_rate"] < 30:
            insights.append(
                {
                    "type": "performance",
                    "message": f"Low cache hit rate ({summary['cache_hit_rate']}%). Consider increasing cache TTL or reviewing caching strategy.",
                    "severity": "medium",
                }
            )
        elif summary["cache_hit_rate"] > 80:
            insights.append(
                {
                    "type": "performance",
                    "message": f"Excellent cache hit rate ({summary['cache_hit_rate']}%)!",
                    "severity": "info",
                }
            )

        # Check success rate
        if summary["success_rate"] < 95:
            insights.append(
                {
                    "type": "reliability",
                    "message": f"Success rate is {summary['success_rate']}%. Review error patterns.",
                    "severity": "high" if summary["success_rate"] < 90 else "medium",
                }
            )

        # Check average response time
        if summary["average_response_time"] > 2.0:
            insights.append(
                {
                    "type": "performance",
                    "message": f"High average response time ({summary['average_response_time']}s). Consider optimizing requests.",
                    "severity": "medium",
                }
            )

        # Check for frequent errors
        error_breakdown = summary.get("error_breakdown", {})
        if error_breakdown:
            most_common_error = max(error_breakdown.items(), key=lambda x: x[1])
            if (
                most_common_error[1] > len(self.metrics) * 0.1
            ):  # More than 10% of requests
                insights.append(
                    {
                        "type": "reliability",
                        "message": f"Frequent {most_common_error[0]} errors ({most_common_error[1]} occurrences). Investigate root cause.",
                        "severity": "high",
                    }
                )

        return {
            "insights": insights,
            "recommendations": self._generate_recommendations(insights),
        }

    def _generate_recommendations(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on insights"""
        recommendations = []

        for insight in insights:
            if insight["type"] == "performance":
                if "cache" in insight["message"].lower():
                    recommendations.append(
                        "Consider increasing cache TTL or enabling caching if disabled"
                    )
                elif "response time" in insight["message"].lower():
                    recommendations.append(
                        "Review API call patterns and consider request batching"
                    )
            elif insight["type"] == "reliability":
                if "success rate" in insight["message"].lower():
                    recommendations.append(
                        "Implement retry logic for transient failures"
                    )
                elif "error" in insight["message"].lower():
                    recommendations.append(
                        "Add error handling and monitoring for frequent error types"
                    )

        # Add general recommendations
        if not recommendations:
            recommendations.append("Monitor metrics regularly for performance trends")

        return recommendations
