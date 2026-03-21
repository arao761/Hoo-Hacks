# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/worker.py
# python
import logging
import time

from models import OutputMetadata, OutputStatus, OutputType
from redis_client import dequeue_job, save_output_metadata
from gemini_client import expand_topic_with_gemini
from storage import upload_media_and_get_cdn_url

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
        # 1) Prompt expansion via Gemini (Person 2 scope)
        prompt_struct = expand_topic_with_gemini(topic, output_type)

        # 2) Call actual media generators (Person 3)
        # For now, simulate some bytes so infra + frontend can integrate.
        fake_content_bytes = str(prompt_struct).encode("utf-8")

        # 3) Upload to storage → CDN URL (Person 4 will plug real storage)
        cdn_url = upload_media_and_get_cdn_url(
            fake_content_bytes, media_type=output_type_str
        )

        # 4) Save final metadata
        meta.status = OutputStatus.done
        meta.cdn_url = cdn_url
        meta.extra = {"prompt": prompt_struct}
        save_output_metadata(meta)

        logger.info("Job %s completed: %s", job_id, cdn_url)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed", job_id)
        meta.status = OutputStatus.error
        meta.error_message = str(exc)
        save_output_metadata(meta)


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