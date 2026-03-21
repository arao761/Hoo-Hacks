# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/worker.py
# python
import logging
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import OutputMetadata, OutputStatus, OutputType
from redis_client import dequeue_job, save_output_metadata
from gemini_client import expand_topic_with_gemini
from infra import upload_media, publish_progress

# Maps output_type string to MIME type for upload_media
MEDIA_CONTENT_TYPES = {
    "image": "image/png",
    "song":  "audio/mpeg",
    "video": "video/mp4",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("learnlens-worker")


def process_job(job: dict) -> None:
    job_id = job["job_id"]
    topic = job["topic"]
    output_type_str = job["output_type"]
    output_type = OutputType(output_type_str)

    logger.info("Processing job %s - %s (%s)", job_id, topic, output_type_str)

    # mark as processing
    meta = OutputMetadata(
        job_id=job_id,
        topic=topic,
        output_type=output_type,
        status=OutputStatus.processing,
    )
    save_output_metadata(meta)

    try:
        # 1) Prompt expansion via Gemini
        asyncio.run(publish_progress(job_id, "prompted", "Building your prompt..."))
        prompt_struct = expand_topic_with_gemini(topic, output_type)

        # 2) Call actual media generators (Person 3 plugs in here)
        # Stub bytes until Person 3 wires in real generation
        asyncio.run(publish_progress(job_id, "generating", f"Generating your {output_type_str}..."))
        fake_content_bytes = str(prompt_struct).encode("utf-8")

        # 3) Upload to S3 via infra
        asyncio.run(publish_progress(job_id, "uploading", "Almost there..."))
        content_type = MEDIA_CONTENT_TYPES.get(output_type_str, "application/octet-stream")
        cdn_url = upload_media(fake_content_bytes, content_type, job_id)

        # 4) Save final metadata
        meta.status = OutputStatus.done
        meta.cdn_url = cdn_url
        meta.extra = {"prompt": prompt_struct}
        save_output_metadata(meta)

        asyncio.run(publish_progress(job_id, "done", "Ready!", {"cdn_url": cdn_url}))
        logger.info("Job %s completed: %s", job_id, cdn_url)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed", job_id)
        meta.status = OutputStatus.error
        meta.error_message = str(exc)
        save_output_metadata(meta)
        asyncio.run(publish_progress(job_id, "error", str(exc)))


def run_worker_loop(poll_interval: int = 1) -> None:
    logger.info("Worker started, waiting for jobs...")
    while True:
        job = dequeue_job(block=True, timeout=5)
        if not job:
            time.sleep(poll_interval)
            continue

        process_job(job)


if __name__ == "__main__":
    run_worker_loop()