import json
from infra.redis_client import get_redis
from infra.config import QUEUE_KEY


async def enqueue_job(job_id: str, topic: str, output_type: str):
    """
    Called by Person 2's backend after POST /generate.
    Pushes the job onto the Redis queue for the worker to pick up.
    """
    redis = await get_redis()
    payload = json.dumps({"job_id": job_id, "topic": topic, "output_type": output_type})
    await redis.lpush(QUEUE_KEY, payload)


async def dequeue_job(timeout: int = 0) -> dict | None:
    """
    Called by Person 2's worker process (blocking pop).
    Returns the next job dict or None on timeout.
    """
    redis = await get_redis()
    result = await redis.brpop(QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    _, payload = result
    return json.loads(payload)
