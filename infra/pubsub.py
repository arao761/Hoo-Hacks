import json
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
    redis = await get_redis()
    payload = json.dumps({"event": event, "message": message, **data})
    await redis.publish(_channel(job_id), payload)


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
