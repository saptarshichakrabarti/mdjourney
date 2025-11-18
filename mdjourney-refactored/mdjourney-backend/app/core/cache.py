"""
Caching module for the FAIR metadata automation system.
Provides in-memory caching with TTL support for frequently accessed data.
"""

import asyncio
import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEntry:
    """Represents a cached entry with timestamp and TTL."""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def remaining_ttl(self) -> float:
        """Get remaining TTL in seconds."""
        elapsed = time.time() - self.created_at
        return max(0, self.ttl_seconds - elapsed)


class MemoryCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set a value in the cache."""
        async with self._lock:
            ttl = ttl_seconds or self.default_ttl
            self._cache[key] = CacheEntry(value, ttl)

    async def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_count,
                "expired_entries": expired_count,
                "cache_size_bytes": sum(len(str(entry.value)) for entry in self._cache.values())
            }


class FileBasedCache:
    """File-based cache that persists across application restarts."""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache = MemoryCache()

    def _get_cache_file_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Sanitize key for filesystem
        safe_key = "".join(c for c in key if c.isalnum() or c in "._-")
        return self.cache_dir / f"{safe_key}.json"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache (memory first, then file)."""
        # Try memory cache first
        value = await self._memory_cache.get(key)
        if value is not None:
            return value

        # Try file cache
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Check if file cache entry is expired
                if time.time() - data.get('created_at', 0) > data.get('ttl_seconds', 300):
                    cache_file.unlink()  # Remove expired file
                    return None

                # Load into memory cache for faster subsequent access
                await self._memory_cache.set(key, data['value'], data.get('ttl_seconds', 300))
                return data['value']

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")
                cache_file.unlink()  # Remove corrupted file

        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in both memory and file cache."""
        # Set in memory cache
        await self._memory_cache.set(key, value, ttl_seconds)

        # Set in file cache
        cache_file = self._get_cache_file_path(key)
        try:
            cache_data = {
                'value': value,
                'created_at': time.time(),
                'ttl_seconds': ttl_seconds
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except IOError as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")

    async def delete(self, key: str) -> None:
        """Delete a value from both memory and file cache."""
        await self._memory_cache.delete(key)
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            cache_file.unlink()

    async def clear(self) -> None:
        """Clear all cache entries."""
        await self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


# Global cache instances
_schema_cache: Optional[FileBasedCache] = None
_metadata_cache: Optional[FileBasedCache] = None
_project_cache: Optional[MemoryCache] = None


def get_schema_cache() -> FileBasedCache:
    """Get the global schema cache instance."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = FileBasedCache(".cache/schemas")
    return _schema_cache


def get_metadata_cache() -> FileBasedCache:
    """Get the global metadata cache instance."""
    global _metadata_cache
    if _metadata_cache is None:
        _metadata_cache = FileBasedCache(".cache/metadata")
    return _metadata_cache


def get_project_cache() -> MemoryCache:
    """Get the global project cache instance."""
    global _project_cache
    if _project_cache is None:
        _project_cache = MemoryCache(default_ttl=60)  # Short TTL for project listings
    return _project_cache


def cached(ttl_seconds: int = 300, cache_type: str = "memory"):
    """
    Decorator to cache function results.

    Args:
        ttl_seconds: Time to live for cache entries
        cache_type: Type of cache to use ("memory", "schema", "metadata")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Get appropriate cache instance
            if cache_type == "schema":
                cache = get_schema_cache()
            elif cache_type == "metadata":
                cache = get_metadata_cache()
            else:
                cache = get_project_cache()

            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Get appropriate cache instance
            if cache_type == "schema":
                cache = get_schema_cache()
            elif cache_type == "metadata":
                cache = get_metadata_cache()
            else:
                cache = get_project_cache()

            # For sync functions, we need to run async cache operations
            async def _get_cached():
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result

                logger.debug(f"Cache miss for {func.__name__}, executing function")
                result = func(*args, **kwargs)
                await cache.set(cache_key, result, ttl_seconds)
                return result

            # Run the async function in the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _get_cached())
                        return future.result()
                else:
                    return loop.run_until_complete(_get_cached())
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(_get_cached())

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def invalidate_cache_pattern(pattern: str, cache_type: str = "memory") -> int:
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Pattern to match cache keys
        cache_type: Type of cache to invalidate

    Returns:
        Number of entries invalidated
    """
    if cache_type == "schema":
        cache = get_schema_cache()
    elif cache_type == "metadata":
        cache = get_metadata_cache()
    else:
        cache = get_project_cache()

    # For file-based caches, we need to scan files
    if isinstance(cache, FileBasedCache):
        invalidated_count = 0
        for cache_file in cache.cache_dir.glob("*.json"):
            if pattern in cache_file.stem:
                cache_file.unlink()
                invalidated_count += 1
        return invalidated_count
    else:
        # For memory cache, we can't easily pattern match without storing keys
        # For now, just clear the entire cache
        await cache.clear()
        return 0


async def cleanup_all_caches() -> Dict[str, int]:
    """Clean up expired entries from all caches."""
    results = {}

    # Cleanup memory caches
    project_cache = get_project_cache()
    results['project_cache'] = await project_cache.cleanup_expired()

    # File-based caches don't need explicit cleanup as they check expiration on access
    results['schema_cache'] = 0
    results['metadata_cache'] = 0

    return results
