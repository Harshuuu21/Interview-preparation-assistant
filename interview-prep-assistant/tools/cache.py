import json
import time
from typing import Any, Optional

# In-memory cache with TTL (replaces Redis for Streamlit deployment)
_cache: dict[str, dict] = {}


def _cleanup():
    """Remove expired entries."""
    now = time.time()
    expired = [k for k, v in _cache.items() if v["expires"] <= now]
    for k in expired:
        del _cache[k]


def get_cache(key: str) -> Optional[Any]:
    _cleanup()
    entry = _cache.get(key)
    if entry and entry["expires"] > time.time():
        return entry["value"]
    return None


def set_cache(key: str, value: Any, ttl_seconds: int) -> bool:
    try:
        _cache[key] = {
            "value": value,
            "expires": time.time() + ttl_seconds,
        }
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False
