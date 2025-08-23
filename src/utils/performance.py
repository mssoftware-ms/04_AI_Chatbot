"""
Performance utilities and optimization helpers for the WhatsApp AI Chatbot.

This module provides decorators, context managers, and utilities for monitoring
and optimizing application performance, including caching, timing, and resource management.
"""

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar
from datetime import datetime, timedelta
import gc
import psutil
import weakref

logger = logging.getLogger(__name__)

# Type variables for generic decorators
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Awaitable[Any]])


class PerformanceMonitor:
    """Global performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "function_calls": {},
            "timing_data": {},
            "memory_usage": {},
            "cache_stats": {},
            "error_counts": {}
        }
        self._start_time = time.time()
    
    def record_function_call(self, func_name: str, duration: float, success: bool = True) -> None:
        """Record function call metrics."""
        if func_name not in self.metrics["function_calls"]:
            self.metrics["function_calls"][func_name] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "success_count": 0,
                "error_count": 0
            }
        
        stats = self.metrics["function_calls"][func_name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)
        
        if success:
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1
    
    def record_memory_usage(self, checkpoint: str) -> None:
        """Record memory usage at specific checkpoints."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.metrics["memory_usage"][checkpoint] = {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "timestamp": datetime.now().isoformat(),
                "python_objects": len(gc.get_objects())
            }
        except Exception as e:
            logger.warning(f"Failed to record memory usage: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        uptime = time.time() - self._start_time
        
        # Calculate function call summary
        func_summary = {}
        for func_name, stats in self.metrics["function_calls"].items():
            func_summary[func_name] = {
                "calls_per_second": stats["count"] / max(uptime, 1),
                "avg_duration": stats["avg_time"],
                "success_rate": (stats["success_count"] / max(stats["count"], 1)) * 100,
                "total_calls": stats["count"]
            }
        
        return {
            "uptime_seconds": uptime,
            "function_performance": func_summary,
            "memory_checkpoints": self.metrics["memory_usage"],
            "cache_performance": self.metrics["cache_stats"]
        }


# Global performance monitor instance
perf_monitor = PerformanceMonitor()


def timing_decorator(func: F) -> F:
    """Decorator to measure function execution time."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            perf_monitor.record_function_call(
                func.__name__, duration, success
            )
            
            # Log slow functions
            if duration > 1.0:  # More than 1 second
                logger.warning(
                    f"Slow function detected: {func.__name__} took {duration:.2f}s"
                )
    
    return wrapper


def async_timing_decorator(func: AsyncF) -> AsyncF:
    """Decorator to measure async function execution time."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            perf_monitor.record_function_call(
                func.__name__, duration, success
            )
            
            # Log slow async functions
            if duration > 2.0:  # More than 2 seconds for async
                logger.warning(
                    f"Slow async function detected: {func.__name__} took {duration:.2f}s"
                )
    
    return wrapper


class TimingContext:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str, log_threshold: float = 1.0):
        self.name = name
        self.log_threshold = log_threshold
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Record in performance monitor
            perf_monitor.record_function_call(
                self.name, duration, exc_type is None
            )
            
            # Log if above threshold
            if duration > self.log_threshold:
                logger.info(f"Timing [{self.name}]: {duration:.3f}s")


class AsyncTimingContext:
    """Async context manager for timing async code blocks."""
    
    def __init__(self, name: str, log_threshold: float = 2.0):
        self.name = name
        self.log_threshold = log_threshold
        self.start_time: Optional[float] = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Record in performance monitor
            perf_monitor.record_function_call(
                self.name, duration, exc_type is None
            )
            
            # Log if above threshold
            if duration > self.log_threshold:
                logger.info(f"Async Timing [{self.name}]: {duration:.3f}s")


class LRUCache:
    """Simple LRU cache implementation with size limits."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[Any, Any] = {}
        self.access_order: Dict[Any, datetime] = {}
    
    def get(self, key: Any) -> Optional[Any]:
        """Get item from cache."""
        if key in self.cache:
            self.access_order[key] = datetime.now()
            return self.cache[key]
        return None
    
    def put(self, key: Any, value: Any) -> None:
        """Put item in cache with LRU eviction."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.access_order.keys(), key=lambda k: self.access_order[k])
            del self.cache[oldest_key]
            del self.access_order[oldest_key]
        
        self.cache[key] = value
        self.access_order[key] = datetime.now()
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": (len(self.cache) / self.max_size) * 100 if self.max_size > 0 else 0
        }


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        """Decorator to apply circuit breaker pattern."""
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if circuit should be opened
            if self.state == "OPEN":
                if (datetime.now() - self.last_failure_time).total_seconds() > self.reset_timeout:
                    self.state = "HALF_OPEN"
                    logger.info(f"Circuit breaker {func.__name__} moved to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker {func.__name__} is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                
                # Reset on success
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info(f"Circuit breaker {func.__name__} reset to CLOSED")
                
                return result
                
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(
                        f"Circuit breaker {func.__name__} opened after "
                        f"{self.failure_count} failures"
                    )
                
                raise
        
        return wrapper


# Memory management utilities
@asynccontextmanager
async def memory_tracking(checkpoint_name: str):
    """Context manager to track memory usage before and after operations."""
    perf_monitor.record_memory_usage(f"{checkpoint_name}_start")
    
    try:
        yield
    finally:
        perf_monitor.record_memory_usage(f"{checkpoint_name}_end")
        
        # Force garbage collection for accurate measurement
        gc.collect()
        perf_monitor.record_memory_usage(f"{checkpoint_name}_after_gc")


class BatchProcessor:
    """Utility for processing items in batches to optimize performance."""
    
    def __init__(self, batch_size: int = 100, max_concurrent: int = 5):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
    
    async def process_items(
        self,
        items: list,
        processor_func: Callable,
        *args,
        **kwargs
    ) -> list:
        """Process items in batches with concurrency control."""
        results = []
        
        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_batch(batch):
            async with semaphore:
                return await processor_func(batch, *args, **kwargs)
        
        # Execute all batches
        batch_results = await asyncio.gather(
            *[process_batch(batch) for batch in batches],
            return_exceptions=True
        )
        
        # Flatten results
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                logger.error(f"Batch processing error: {batch_result}")
                continue
            
            if isinstance(batch_result, list):
                results.extend(batch_result)
            else:
                results.append(batch_result)
        
        return results


# Convenience functions
def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    return perf_monitor.get_performance_summary()


def reset_performance_metrics() -> None:
    """Reset all performance metrics."""
    global perf_monitor
    perf_monitor = PerformanceMonitor()
    logger.info("Performance metrics reset")


# Export commonly used items
__all__ = [
    'timing_decorator',
    'async_timing_decorator', 
    'TimingContext',
    'AsyncTimingContext',
    'LRUCache',
    'CircuitBreaker',
    'memory_tracking',
    'BatchProcessor',
    'get_performance_metrics',
    'reset_performance_metrics',
    'perf_monitor'
]