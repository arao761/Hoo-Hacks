import json
import redis.asyncio as aioredis
from infra.config import REDIS_URL
from infra.redis_client import get_redis


def _channel(job_id: str) -> str:
    return f"job:{job_id}"


async def publish_progress(job_id: str, event: str, message: str, data: dict = {}):
    """
    Called by Person 3's AI modules after each generation step.

    Events to use (in order):
        "prompted"    - Gemini finished building the prompt
        "generating"  - AI model call started
        "uploading"   - uploading file to S3
        "done"        - generation complete, cdn_url is available in data
        "error"       - something went wrong, message has detail

    Example:
        await publish_progress(job_id, "done", "Your song is ready!", {"cdn_url": "...", "lyrics": "..."})
    """
    # Fresh connection each call so this works correctly when called via
    # asyncio.run() from the synchronous worker (each call has its own event loop)
    client = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        payload = json.dumps({"event": event, "message": message, **data})
        await client.publish(_channel(job_id), payload)
    finally:
        await client.aclose()


async def subscribe_to_job(job_id: str):
    """
    Used internally by the WebSocket handler to listen for job events.
    Yields parsed message dicts until a 'done' or 'error' event is received.
    """
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(_channel(job_id))

    try:
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            msg = json.loads(raw["data"])
            yield msg
            if msg.get("event") in ("done", "error"):
                break
    finally:
        await pubsub.unsubscribe(_channel(job_id))
        await pubsub.aclose()
