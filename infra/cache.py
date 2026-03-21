import json
import re
from infra.redis_client import get_redis
from infra.config import CACHE_TTL


def _cache_key(topic: str, output_type: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower().strip()).strip("-")
    return f"cache:{output_type}:{slug}"


async def check_cache(topic: str, output_type: str) -> dict | None:
    """
    Called by Person 2's worker before running any AI generation.
    Returns cached output dict if it exists, otherwise None.

    Example return value:
        {"cdn_url": "https://...", "lyrics": "...", "topic": "...", "output_type": "..."}
    """
    redis = await get_redis()
    value = await redis.get(_cache_key(topic, output_type))
    if value:
        return json.loads(value)
    return None


async def set_cache(topic: str, output_type: str, output: dict):
    """
    Called by Person 2's worker after a successful generation.
    Stores the output dict so future identical requests skip generation.

    Args:
        output: dict with at minimum {"cdn_url": "..."}
                for songs also include {"lyrics": "..."}
    """
    redis = await get_redis()
    await redis.set(
        _cache_key(topic, output_type),
        json.dumps(output),
        ex=CACHE_TTL,
    )
