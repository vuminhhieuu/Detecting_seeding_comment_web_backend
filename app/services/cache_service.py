import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import hashlib

class CacheService:
    """Simple in-memory cache service for API responses"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = 3600  # 1 hour in seconds
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from data"""
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires_at']:
                return entry['value']
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active_entries = sum(
            1 for entry in self.cache.values()
            if now < entry['expires_at']
        )
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': len(self.cache) - active_entries,
            'memory_usage_mb': len(str(self.cache)) / (1024 * 1024)
        }

# Global cache instance
cache_service = CacheService()