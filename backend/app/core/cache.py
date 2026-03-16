"""
Caching utilities for performance optimization
"""

import hashlib
import pickle
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..config import settings

# Global Redis client
_redis_client: Any | None = None


async def get_redis() -> Any | None:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None and REDIS_AVAILABLE:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL)
        except Exception:
            pass
    return _redis_client


class Cache:
    """Simple caching wrapper with Redis fallback"""

    _local_cache: dict = {}
    _local_ttl: dict = {}

    @classmethod
    async def get(cls, key: str) -> Any | None:
        """Get value from cache"""
        # Try Redis first
        if REDIS_AVAILABLE:
            r = await get_redis()
            if r:
                try:
                    value = await r.get(key)
                    if value:
                        return pickle.loads(value)
                except Exception:
                    pass

        # Fall back to local cache
        if key in cls._local_cache:
            expires_at = cls._local_ttl.get(key)
            if expires_at and datetime.utcnow() < expires_at:
                return cls._local_cache[key]
            else:
                # Expired, clean up
                cls._local_cache.pop(key, None)
                cls._local_ttl.pop(key, None)

        return None

    @classmethod
    async def set(
        cls,
        key: str,
        value: Any,
        ttl: int = 300,  # 5 minutes default
    ) -> bool:
        """Set value in cache"""
        # Try Redis first
        if REDIS_AVAILABLE:
            r = await get_redis()
            if r:
                try:
                    await r.setex(key, ttl, pickle.dumps(value))
                    return True
                except Exception:
                    pass

        # Fall back to local cache
        cls._local_cache[key] = value
        cls._local_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return True

    @classmethod
    async def delete(cls, key: str) -> bool:
        """Delete value from cache"""
        # Try Redis first
        if REDIS_AVAILABLE:
            r = await get_redis()
            if r:
                try:
                    await r.delete(key)
                except Exception:
                    pass

        # Clean up local cache
        cls._local_cache.pop(key, None)
        cls._local_ttl.pop(key, None)
        return True

    @classmethod
    async def clear_pattern(cls, pattern: str) -> int:
        """Clear all keys matching pattern"""
        count = 0

        if REDIS_AVAILABLE:
            r = await get_redis()
            if r:
                try:
                    keys = await r.keys(pattern)
                    if keys:
                        count = await r.delete(*keys)
                except Exception:
                    pass

        # Clear local cache keys matching pattern
        keys_to_delete = [
            k for k in cls._local_cache.keys() if pattern.replace("*", "") in k
        ]
        for k in keys_to_delete:
            cls._local_cache.pop(k, None)
            cls._local_ttl.pop(k, None)
            count += 1

        return count


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Usage:
        @cached(ttl=60, key_prefix="agent")
        async def get_agent(agent_id: str):
            return await db.get_agent(agent_id)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)

            # Try to get from cache
            cached_value = await Cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await Cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def _generate_cache_key(
    prefix: str,
    func_name: str,
    args: tuple,
    kwargs: dict,
) -> str:
    """Generate a cache key from function arguments"""
    key_parts = [prefix, func_name]

    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))

    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")

    key = ":".join(key_parts)

    # Hash if too long
    if len(key) > 200:
        return f"{prefix}:{hashlib.md5(key.encode()).hexdigest()}"

    return key


class Memoize:
    """In-memory memoization for expensive computations"""

    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))

            # Check cache
            if key in self.cache:
                timestamp = self.timestamps.get(key)
                if timestamp and datetime.utcnow().timestamp() - timestamp < self.ttl:
                    return self.cache[key]

            # Execute and cache
            result = await func(*args, **kwargs)

            # Manage cache size
            if len(self.cache) >= self.maxsize:
                oldest_key = min(self.timestamps, key=self.timestamps.get)
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]

            self.cache[key] = result
            self.timestamps[key] = datetime.utcnow().timestamp()

            return result

        return wrapper


# Cache invalidation helpers
async def invalidate_agent_cache(agent_id: str):
    """Invalidate all cache entries for an agent"""
    await Cache.clear_pattern(f"*agent*{agent_id}*")


async def invalidate_task_cache(task_id: str):
    """Invalidate all cache entries for a task"""
    await Cache.clear_pattern(f"*task*{task_id}*")


async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user"""
    await Cache.clear_pattern(f"*user*{user_id}*")
