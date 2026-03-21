import json
from infra.redis_client import get_redis
from infra.config import JOB_TTL


def _job_key(job_id: str) -> str:
    return f"job_output:{job_id}"


async def store_output(job_id: str, output: dict):
    """
    Called by Person 2's worker after generation completes.
    Stores job output so the share page (GET /output/{id}) can retrieve it.

    Args:
        output: dict with at minimum {"cdn_url": "...", "topic": "...", "output_type": "..."}
                for songs also include {"lyrics": "..."}
    """
    redis = await get_redis()
    await redis.set(_job_key(job_id), json.dumps(output), ex=JOB_TTL)


async def get_output(job_id: str) -> dict | None:
    """
    Called by Person 2's GET /output/{job_id} endpoint.
    Returns the stored output dict or None if not found / expired.
    """
    redis = await get_redis()
    value = await redis.get(_job_key(job_id))
    if value:
        return json.loads(value)
    return None
