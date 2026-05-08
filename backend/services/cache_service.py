"""
Cache Service: simple file-based caching.
"""

import json
from pathlib import Path
from typing import Any, Optional
import logging

from backend.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class CacheService:
    """Simple file-based cache for API responses."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Args:
            cache_dir: Directory to store cache files (default: config.CACHE_DIR)
        """
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Cache read failed for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Cache write failed for {key}: {e}")
    
    def clear_all(self) -> None:
        """Clear all cache files."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
