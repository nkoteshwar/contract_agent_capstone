import json
import hashlib
import logging
from typing import Any, Optional, Dict
from functools import wraps
import os

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class RedisCache:
    """Redis-based caching for CUAD analysis results"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis with fallback to in-memory cache"""
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory cache: {e}")
            self.redis_client = InMemoryCache()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cached value with TTL"""
        try:
            serialized = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()

class InMemoryCache:
    """Fallback in-memory cache"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)
    
    def setex(self, key: str, ttl: int, value: str) -> bool:
        self._cache[key] = value
        return True
    
    def ping(self):
        return True

# Global cache instance
cache = RedisCache()

def cache_result(prefix: str, ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache.generate_key(prefix, *args, *kwargs.values())
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator