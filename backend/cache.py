import json
import os
import hashlib
from pathlib import Path
from typing import Optional, Any

CACHE_DIR = Path("AetherTrip/.cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_key(func_name: str, *args, **kwargs) -> str:
    """Generates a unique cache key based on function name and arguments."""
    content = f"{func_name}:{str(args)}:{str(kwargs)}"
    return hashlib.md5(content.encode()).hexdigest()

def load_from_cache(key: str) -> Optional[Any]:
    """Loads data from cache if it exists."""
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_to_cache(key: str, data: Any):
    """Saves data to cache."""
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save cache: {e}")
