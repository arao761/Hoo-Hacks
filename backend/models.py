# python
# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/models.py
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class OutputType(str, Enum):
    song = "song"
    video = "video"


class LanguageCode(str, Enum):
    en = "en"
    es = "es"
    zh = "zh"
    hi = "hi"
    de = "de"
    it = "it"


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    output_type: OutputType
    language: LanguageCode = LanguageCode.en


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