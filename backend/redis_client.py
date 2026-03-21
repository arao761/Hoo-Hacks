# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/redis_client.py
# python
import json
from typing import Optional

import redis

from config import get_settings
from models import OutputMetadata

settings = get_settings()

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def enqueue_job(job_payload: dict) -> None:
    """Push a job payload onto the Redis queue."""
    redis_client.rpush(settings.redis_queue_key, json.dumps(job_payload))


def dequeue_job(block: bool = True, timeout: int = 5) -> Optional[dict]:
    """Pop a job from the Redis queue."""
    if block:
        item = redis_client.blpop(settings.redis_queue_key, timeout=timeout)
        if not item:
            return None
        _, raw = item
    else:
        raw = redis_client.lpop(settings.redis_queue_key)
        if not raw:
            return None
    return json.loads(raw)


def save_output_metadata(metadata: OutputMetadata) -> None:
    """Store output metadata with TTL."""
    key = f"{settings.redis_output_prefix}{metadata.job_id}"
    redis_client.setex(key, settings.job_ttl_seconds, metadata.model_dump_json())


def get_output_metadata(job_id: str) -> Optional[OutputMetadata]:
    """Retrieve output metadata for a given job id."""
    key = f"{settings.redis_output_prefix}{job_id}"
    raw = redis_client.get(key)
    if not raw:
        return None
    return OutputMetadata.model_validate_json(raw)