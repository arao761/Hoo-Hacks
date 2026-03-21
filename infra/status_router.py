from fastapi import APIRouter
from fastapi.responses import JSONResponse
from infra.job_store import get_output

router = APIRouter()


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    HTTP polling fallback for Person 1 to use if the WebSocket fails to connect.

    Person 1 polls this every 2 seconds after POST /generate.
    Returns 202 while the job is still running, 200 when done.

    Response shapes:
        Still running:  { "status": "pending" }
        Done:           { "status": "done", "cdn_url": "...", "topic": "...", "output_type": "...", "lyrics": "..." }
        Not found:      { "status": "not_found" }
    """
    output = await get_output(job_id)

    if output is None:
        # Job hasn't finished yet (or job_id is wrong)
        return JSONResponse(status_code=202, content={"status": "pending"})

    return JSONResponse(status_code=200, content={"status": "done", **output})
