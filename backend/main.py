# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/main.py
# python
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from models import (
    GenerateRequest,
    GenerateResponse,
    OutputMetadata,
    OutputStatus,
)
from redis_client import enqueue_job, get_output_metadata, save_output_metadata

settings = get_settings()
app = FastAPI(title="LearnLens Backend (Person 2)")


# CORS so Person 1 can hit this from Next.js (adjust origins in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["https://your-frontend.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """
    Simple healthcheck for infra / debugging.
    """
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    """
    Phase 1 — API Foundation
    - Creates job ID
    - Enqueues job payload to Redis
    - Seeds 'pending' metadata
    """
    job_id = str(uuid.uuid4())

    job_payload = {
        "job_id": job_id,
        "topic": req.topic,
        "output_type": req.output_type.value,
    }

    # 1) enqueue for worker
    enqueue_job(job_payload)

    # 2) seed metadata as pending so frontend can show "in progress"
    meta = OutputMetadata(
        job_id=job_id,
        topic=req.topic,
        output_type=req.output_type,
        status=OutputStatus.pending,
    )
    save_output_metadata(meta)

    return GenerateResponse(job_id=job_id)


@app.get("/output/{job_id}", response_model=OutputMetadata)
async def output(job_id: str) -> OutputMetadata:
    """
    Returns current metadata (status, cdn_url, etc.) for a job.
    Frontend + WS layer can poll/use this.
    """
    meta = get_output_metadata(job_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")
    return meta