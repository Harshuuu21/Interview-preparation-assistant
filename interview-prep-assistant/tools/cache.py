import redis
import json
import os
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL)
    # Test connection
    redis_client.ping()
except Exception as e:
    print(f"Failed to connect to Redis at {REDIS_URL}: {e}")
    redis_client = None

def get_cache(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        val = redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        print(f"Redis get error: {e}")
    return None

def set_cache(key: str, value: Any, ttl_seconds: int) -> bool:
    if not redis_client:
        return False
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(value))
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False
