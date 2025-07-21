"""
Cache adapter for logging system.

Provides an adapter between the existing CacheService and the
CacheServiceInterface required by the logging system.
"""

import logging
from typing import Optional, Any

from ...core.logging import CacheServiceInterface
from ...database.redis_factory import get_redis_manager, get_prefixed_key

logger = logging.getLogger(__name__)


class LoggingCacheAdapter(CacheServiceInterface):
    """
    Cache adapter for logging system.

    Implements CacheServiceInterface using the Redis factory pattern
    to provide caching for the logging system.
    """

    def __init__(self):
        """Initialize cache adapter."""
        pass

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            redis_manager = await get_redis_manager()
            prefixed_key = get_prefixed_key(f"log:{key}")

            result = await redis_manager.get(prefixed_key)
            if result:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")

            return result

        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """
        Set value in cache with optional expiration.

        Args:
            key: Cache key
            value: Value to cache
            expire: Optional expiration time in seconds
        """
        try:
            redis_manager = await get_redis_manager()
            prefixed_key = get_prefixed_key(f"log:{key}")

            # Ensure Redis is connected
            if not await redis_manager.is_connected():
                await redis_manager.connect()

            # Use default TTL if expire is None
            ttl = expire if expire is not None else 300  # 5 minutes default

            success = await redis_manager.set(prefixed_key, value, ttl=ttl)

            if success:
                logger.debug(f"Cache set successful for key: {key} (TTL: {ttl})")
            else:
                logger.warning(f"Cache set failed for key: {key}")

        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            import traceback

            logger.warning(f"Cache set exception traceback: {traceback.format_exc()}")

    async def delete(self, key: str) -> None:
        """
        Delete value from cache by key.

        Args:
            key: Cache key to delete
        """
        try:
            redis_manager = await get_redis_manager()
            prefixed_key = get_prefixed_key(f"log:{key}")

            result = await redis_manager.delete(prefixed_key)
            if result:
                logger.debug(f"Cache delete successful for key: {key}")
            else:
                logger.debug(f"Cache key not found for deletion: {key}")

        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")

    async def clear_pattern(self, pattern: str) -> None:
        """
        Clear all cache keys matching the pattern.

        Args:
            pattern: Pattern to match (e.g., "log_stats:*")
        """
        try:
            redis_manager = await get_redis_manager()

            # For simplicity, we'll clear specific patterns used by logging system
            # This avoids needing SCAN operations which may not be available in all Redis implementations
            patterns_to_clear = []

            if pattern == "log_stats:*":
                # Clear commonly used stats patterns
                for hours in [1, 6, 12, 24, 48, 168]:  # Common hour ranges
                    patterns_to_clear.append(f"log:log_stats:{hours}h")
            elif pattern == "log_dashboard:*":
                # Clear commonly used dashboard patterns
                for hours in [1, 6, 12, 24, 48, 168]:  # Common hour ranges
                    patterns_to_clear.append(f"log:log_dashboard:{hours}h")
            elif pattern == "log_*":
                # Clear all common logging patterns
                for hours in [1, 6, 12, 24, 48, 168]:
                    patterns_to_clear.extend(
                        [f"log:log_stats:{hours}h", f"log:log_dashboard:{hours}h"]
                    )
            else:
                # For other patterns, try to clear the direct pattern
                patterns_to_clear.append(get_prefixed_key(f"log:{pattern}"))

            # Delete all identified keys
            cleared_count = 0
            for key in patterns_to_clear:
                deleted = await redis_manager.delete(key)
                if deleted:
                    cleared_count += 1

            logger.debug(f"Cleared {cleared_count} cache keys for pattern: {pattern}")

        except Exception as e:
            logger.warning(f"Cache clear pattern failed for pattern {pattern}: {e}")


# Create singleton instance
_logging_cache_adapter: Optional[LoggingCacheAdapter] = None


async def get_logging_cache_adapter() -> Optional[LoggingCacheAdapter]:
    """
    Get logging cache adapter instance.

    Returns:
        LoggingCacheAdapter instance or None if Redis is not available
    """
    global _logging_cache_adapter

    if _logging_cache_adapter is None:
        try:
            # Test Redis connection first
            redis_manager = await get_redis_manager()
            await redis_manager.health_check()

            _logging_cache_adapter = LoggingCacheAdapter()
            logger.info("Logging cache adapter initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize logging cache adapter: {e}")
            return None

    return _logging_cache_adapter
