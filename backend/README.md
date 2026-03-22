#### LearnLens Backend (Person 2 — FastAPI · Python · Job Orchestration)

This folder contains the **backend service** for LearnLens, owned by **Person 2**.  
Responsibilities: FastAPI API, job orchestration, prompt structuring for Gemini, and coordination with Redis + worker.  
No frontend code lives here.

---

## High-Level Flow

1. Frontend calls `POST /generate` with a topic and output type (`image | song | video`).
2. Backend creates a `job_id`, enqueues a job in Redis, and returns the `job_id` immediately.
3. Worker process (always running) dequeues jobs, expands the topic into a structured prompt, calls media generators (stubbed), uploads bytes via `storage.py` (stubbed), and writes output metadata (including a fake CDN URL) back to Redis.
4. Frontend / WebSocket layer can call `GET /output/{job_id}` to get:
   - status: `pending | processing | done | error`
   - cdn_url (once done)
   - extra prompt metadata

Infra (Person 4) and AI integrations (Person 3) can plug into the clear interfaces exposed here.

---

## Project Structure

```text
backend/
  ├── main.py          # FastAPI app: /generate, /output/{id}
  ├── worker.py        # Long-running worker process
  ├── models.py        # Pydantic models + enums
  ├── redis_client.py  # Redis queue + metadata helpers
  ├── config.py        # Env-based configuration
  ├── gemini_client.py # Prompt engineering stub (Gemini-facing shape)
  ├── storage.py       # Media upload → CDN URL interface (stub)
  └── README.md        # This file
```

---

## Endpoints (for Person 1, 3, 4)

### `POST /generate`

**Description**  
Create a new generation job and enqueue it.

**Request body**

```json
{
  "topic": "Photosynthesis",
  "output_type": "image"
}
```

- `output_type`: `"image" | "song" | "video"`

**Response (200)**

```json
{
  "job_id": "9b73d5ac-1eed-4a67-9df3-170b1f3c7e2b"
}
```

### `GET /output/{job_id}`

**Description**  
Return the current status and metadata for a given job.

**Response (example when done)**

```json
{
  "job_id": "9b73d5ac-1eed-4a67-9df3-170b1f3c7e2b",
  "topic": "Photosynthesis",
  "output_type": "image",
  "status": "done",
  "cdn_url": "https://cdn.example.com/image/abc123.png",
  "error_message": null,
  "extra": {
    "prompt": {
      "type": "image",
      "visual_description": "Detailed educational illustration about Photosynthesis",
      "pedagogy_notes": "Explain concept with labels, arrows, and simple language."
    }
  }
}
```

---

## Worker Process

File: `worker.py`

- Consumes jobs from the Redis queue.
- Uses `gemini_client.expand_topic_with_gemini()` to generate **structured prompts** from a raw topic.
- Simulates a media generation step (Person 3 will replace with real AI calls).
- Uses `storage.upload_media_and_get_cdn_url()` to get a CDN URL (Person 4 will wire to R2/S3).
- Writes final `OutputMetadata` back to Redis.

---

## Prompt Engineering (Person 2 Scope)

File: `gemini_client.py`

- Defines how a raw topic becomes a **structured prompt object** depending on `OutputType`:
  - `image`: visual description + educational framing.
  - `song`: style, mood, lyrics brief.
  - `video`: scene sequence + narration outline.
- Real Gemini API calls can be added later without changing the rest of the backend.

---

## Storage Interface (Infra Hook)

File: `storage.py`

- Function: `upload_media_and_get_cdn_url(content_bytes, media_type)`.
- Currently returns a **fake** CDN URL like:

  `https://cdn.example.com/image/<random>.png`

- Infra (Person 4) will:
  - Upload `content_bytes` to Cloudflare R2 or S3.
  - Generate a real public (or signed) CDN URL.
  - Implement caching / TTL policies.

---

## Redis Usage

File: `redis_client.py`

- Queue key: `jobs:queue`
- Output metadata key: `output:{job_id}` (24h TTL by default)
- Stores/reads `OutputMetadata` JSON objects

This is the main contract between:
- API ↔ worker
- Worker ↔ WebSocket layer

---

## Configuration

File: `config.py`

Environment variables:

- `REDIS_URL` (default: `redis://localhost:6379/0`)
- `CDN_BASE_URL` (optional, default: `https://cdn.example.com`)

Example:

```env
REDIS_URL=redis://localhost:6379/0
CDN_BASE_URL=https://your-real-cdn.example.com
```

---

## Running Locally (Mac / VS Code)

From the `backend` directory:

```bash
# 1. Install dependencies
pip install fastapi uvicorn redis pydantic

# 2. Start FastAPI app (Person 2 backend)
uvicorn main:app --reload

# 3. In another terminal, start the worker loop
python worker.py
```

---

## Quick Test with curl

```bash
# Create a job
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"World War 2","output_type":"video"}'

# Poll output (replace <job_id>)
curl http://127.0.0.1:8000/output/<job_id>
```

## Running Tests

From the `backend` directory:

```bash
pytest
```