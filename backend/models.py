# python
# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/models.py
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class OutputType(str, Enum):
    image = "image"
    song = "song"
    video = "video"


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    output_type: OutputType


class GenerateResponse(BaseModel):
    job_id: str


class OutputStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class OutputMetadata(BaseModel):
    job_id: str
    topic: str
    output_type: OutputType
    status: OutputStatus
    cdn_url: Optional[str] = None
    error_message: Optional[str] = None
    extra: Dict[str, Any] = {}