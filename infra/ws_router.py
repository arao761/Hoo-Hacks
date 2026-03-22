import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from infra.pubsub import subscribe_to_job
from infra.job_store import get_output

router = APIRouter()

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    Person 1 connects here immediately after receiving a job_id from POST /generate.
    Streams progress events until the job is done or errors out.

    Message shape sent to frontend:
        { "event": "prompted",    "message": "Building your prompt..." }
        { "event": "generating",  "message": "Generating your song..." }
        { "event": "uploading",   "message": "Almost there..."         }
        { "event": "done",        "message": "Ready!", "cdn_url": "https://...", "lyrics": "..." }
        { "event": "error",       "message": "Something went wrong."   }
    """
    await websocket.accept()

    # If the job already finished before the client connected, send result immediately
    cached = await get_output(job_id)
    if cached and cached.get("status") == "done":
        await websocket.send_text(json.dumps({"event": "done", "message": "Ready!", **cached}))
        await websocket.close()
        return

    try:
        async for msg in subscribe_to_job(job_id):
            await websocket.send_text(json.dumps(msg))
            if msg.get("event") in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
