"""
Performance monitoring and optimization configuration for the FAIR metadata automation system.
"""

import logging
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceConfig:
    """Configuration for performance optimizations."""

    # Cache configurations
    CACHE_CONFIG = {
        "schema_cache": {
            "enabled": True,
            "ttl_seconds": 3600,  # 1 hour
            "max_size": 1000,
            "persist_to_disk": True,
        },
        "metadata_cache": {
            "enabled": True,
            "ttl_seconds": 300,   # 5 minutes
            "max_size": 5000,
            "persist_to_disk": True,
        },
        "project_cache": {
            "enabled": True,
            "ttl_seconds": 60,    # 1 minute
            "max_size": 100,
            "persist_to_disk": False,
        },
    }

    # Async processing configurations
    ASYNC_CONFIG = {
        "file_processing": {
            "enabled": True,
            "max_concurrent_files": 10,
            "chunk_size": 4096,
            "use_thread_pool": True,
        },
        "metadata_generation": {
            "enabled": True,
            "max_concurrent_generations": 5,
            "use_background_tasks": True,
        },
        "schema_loading": {
            "enabled": True,
            "preload_common_schemas": True,
            "use_thread_pool": True,
        },
    }

    # Background task configurations
    BACKGROUND_TASKS = {
        "enabled": True,
        "max_concurrent_tasks": 5,
        "task_timeout_seconds": 300,
        "cleanup_interval_hours": 24,
        "max_task_history": 1000,
    }

    # API optimization configurations
    API_OPTIMIZATION = {
        "response_compression": True,
        "etag_support": True,
        "request_batching": True,
        "connection_pooling": True,
        "keep_alive": True,
    }

    # Frontend optimization configurations
    FRONTEND_OPTIMIZATION = {
        "api_caching": {
            "enabled": True,
            "default_ttl_ms": 300000,  # 5 minutes
            "projects_ttl_ms": 60000,   # 1 minute
            "datasets_ttl_ms": 120000, # 2 minutes
            "schemas_ttl_ms": 1800000, # 30 minutes
            "metadata_ttl_ms": 300000, # 5 minutes
        },
        "preloading": {
            "enabled": True,
            "preload_on_startup": True,
            "preload_common_data": True,
        },
        "lazy_loading": {
            "enabled": True,
            "load_metadata_on_demand": True,
        },
    }

    # Performance monitoring configurations
    MONITORING = {
        "enabled": True,
        "log_slow_requests": True,
        "slow_request_threshold_ms": 1000,
        "log_cache_stats": True,
        "log_performance_metrics": True,
    }

    @classmethod
    def get_cache_config(cls, cache_type: str) -> Dict[str, Any]:
        """Get cache configuration for a specific cache type."""
        return cls.CACHE_CONFIG.get(cache_type, {})

    @classmethod
    def get_async_config(cls, operation_type: str) -> Dict[str, Any]:
        """Get async configuration for a specific operation type."""
        return cls.ASYNC_CONFIG.get(operation_type, {})

    @classmethod
    def is_feature_enabled(cls, feature_path: str) -> bool:
        """
        Check if a feature is enabled using dot notation.

        Args:
            feature_path: Feature path like "cache.schema_cache.enabled"

        Returns:
            True if feature is enabled, False otherwise
        """
        try:
            parts = feature_path.split('.')
            config = cls.__dict__

            for part in parts:
                if isinstance(config, dict):
                    config = config.get(part)
                else:
                    config = getattr(config, part, None)

                if config is None:
                    return False

            return bool(config)
        except Exception:
            return False

    @classmethod
    def get_performance_settings(cls) -> Dict[str, Any]:
        """Get all performance settings as a dictionary."""
        return {
            "cache": cls.CACHE_CONFIG,
            "async": cls.ASYNC_CONFIG,
            "background_tasks": cls.BACKGROUND_TASKS,
            "api_optimization": cls.API_OPTIMIZATION,
            "frontend_optimization": cls.FRONTEND_OPTIMIZATION,
            "monitoring": cls.MONITORING,
        }


class PerformanceMonitor:
    """Monitor performance metrics and provide optimization suggestions."""

    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.slow_requests: list = []
        self.cache_stats: Dict[str, Any] = {}

    def record_request_time(self, endpoint: str, duration_ms: float):
        """Record request duration for monitoring."""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
            }

        stats = self.metrics[endpoint]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["min_time"] = min(stats["min_time"], duration_ms)
        stats["max_time"] = max(stats["max_time"], duration_ms)

        # Log slow requests
        if PerformanceConfig.MONITORING.get("log_slow_requests", True):
            threshold = PerformanceConfig.MONITORING.get("slow_request_threshold_ms", 1000)
            if duration_ms > threshold:
                self.slow_requests.append({
                    "endpoint": endpoint,
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                })
                logger.warning(f"Slow request detected: {endpoint} took {duration_ms:.2f}ms")

    def record_cache_stats(self, cache_type: str, hits: int, misses: int):
        """Record cache statistics."""
        self.cache_stats[cache_type] = {
            "hits": hits,
            "misses": misses,
            "hit_rate": hits / (hits + misses) if (hits + misses) > 0 else 0,
        }

        if PerformanceConfig.MONITORING.get("log_cache_stats", True):
            hit_rate = self.cache_stats[cache_type]["hit_rate"]
            logger.info(f"Cache stats for {cache_type}: {hit_rate:.2%} hit rate ({hits} hits, {misses} misses)")

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report."""
        report = {
            "request_metrics": self.metrics,
            "cache_stats": self.cache_stats,
            "slow_requests": self.slow_requests[-10:],  # Last 10 slow requests
            "optimization_suggestions": self._get_optimization_suggestions(),
        }

        return report

    def _get_optimization_suggestions(self) -> list:
        """Generate optimization suggestions based on metrics."""
        suggestions = []

        # Check for slow endpoints
        for endpoint, stats in self.metrics.items():
            if stats["avg_time"] > 1000:  # More than 1 second average
                suggestions.append({
                    "type": "slow_endpoint",
                    "endpoint": endpoint,
                    "avg_time_ms": stats["avg_time"],
                    "suggestion": f"Consider caching or optimizing {endpoint}",
                })

        # Check cache hit rates
        for cache_type, stats in self.cache_stats.items():
            if stats["hit_rate"] < 0.5:  # Less than 50% hit rate
                suggestions.append({
                    "type": "low_cache_hit_rate",
                    "cache_type": cache_type,
                    "hit_rate": stats["hit_rate"],
                    "suggestion": f"Increase TTL or improve cache key strategy for {cache_type}",
                })

        return suggestions


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_performance_config() -> PerformanceConfig:
    """Get the performance configuration."""
    return PerformanceConfig


# Environment-based configuration overrides
def load_performance_config_from_env():
    """Load performance configuration from environment variables."""
    config = PerformanceConfig()

    # Override cache settings from environment
    if os.getenv("MDJOURNEY_CACHE_ENABLED"):
        config.CACHE_CONFIG["schema_cache"]["enabled"] = os.getenv("MDJOURNEY_CACHE_ENABLED").lower() == "true"

    if os.getenv("MDJOURNEY_SCHEMA_CACHE_TTL"):
        config.CACHE_CONFIG["schema_cache"]["ttl_seconds"] = int(os.getenv("MDJOURNEY_SCHEMA_CACHE_TTL"))

    if os.getenv("MDJOURNEY_METADATA_CACHE_TTL"):
        config.CACHE_CONFIG["metadata_cache"]["ttl_seconds"] = int(os.getenv("MDJOURNEY_METADATA_CACHE_TTL"))

    # Override async settings from environment
    if os.getenv("MDJOURNEY_ASYNC_ENABLED"):
        config.ASYNC_CONFIG["file_processing"]["enabled"] = os.getenv("MDJOURNEY_ASYNC_ENABLED").lower() == "true"

    if os.getenv("MDJOURNEY_MAX_CONCURRENT_FILES"):
        config.ASYNC_CONFIG["file_processing"]["max_concurrent_files"] = int(os.getenv("MDJOURNEY_MAX_CONCURRENT_FILES"))

    # Override background task settings from environment
    if os.getenv("MDJOURNEY_BACKGROUND_TASKS_ENABLED"):
        config.BACKGROUND_TASKS["enabled"] = os.getenv("MDJOURNEY_BACKGROUND_TASKS_ENABLED").lower() == "true"

    if os.getenv("MDJOURNEY_MAX_CONCURRENT_TASKS"):
        config.BACKGROUND_TASKS["max_concurrent_tasks"] = int(os.getenv("MDJOURNEY_MAX_CONCURRENT_TASKS"))

    logger.info("Performance configuration loaded from environment variables")
    return config


# Initialize configuration on import
load_performance_config_from_env()
