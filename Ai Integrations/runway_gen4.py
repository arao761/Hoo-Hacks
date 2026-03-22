"""Runway Gen-4 video generation (official ``runwayml`` SDK).

Supports:
  - **Text → video** via ``text_to_video`` (default model ``gen4.5``).
  - **Image → video** via ``image_to_video`` (default ``gen4.5``); ``prompt_image`` may be
    an HTTPS URL or a ``data:image/...;base64,...`` URI.

Environment:
  RUNWAYML_API_SECRET — API key (alias: RUNWAY_API_KEY)

Optional:
  RUNWAY_TEXT_TO_VIDEO_MODEL  (default: gen4.5)
  RUNWAY_IMAGE_TO_VIDEO_MODEL (default: gen4.5)

Docs: https://docs.dev.runwayml.com/guides/using-the-api/
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Literal, Optional

import httpx
from runwayml import RunwayML, TaskFailedError, TaskTimeoutError
from runwayml.types.task_retrieve_response import Succeeded

from progress_events import VideoProgressCallback, emit_video_progress

DEFAULT_TEXT_MODEL = os.environ.get("RUNWAY_TEXT_TO_VIDEO_MODEL", "gen4.5").strip()
DEFAULT_IMAGE_MODEL = os.environ.get("RUNWAY_IMAGE_TO_VIDEO_MODEL", "gen4.5").strip()

TextToVideoRatio = Literal["1280:720", "720:1280"]
ImageToVideoRatio = Literal[
    "1280:720",
    "720:1280",
    "1104:832",
    "960:960",
    "832:1104",
    "1584:672",
]


@dataclass(frozen=True)
class RunwayGen4VideoResult:
    video_bytes: bytes
    mime_type: str
    model: str
    task_id: str
    """First CDN URL from Runway (short-lived; download and re-host for production)."""
    output_url: str


def _api_secret() -> str:
    s = os.environ.get("RUNWAYML_API_SECRET", "").strip() or os.environ.get("RUNWAY_API_KEY", "").strip()
    if not s:
        raise RuntimeError(
            "Runway API key missing: set RUNWAYML_API_SECRET (or RUNWAY_API_KEY) in .env"
        )
    return s


def _client() -> RunwayML:
    return RunwayML(api_key=_api_secret())


def image_bytes_to_data_uri(data: bytes, mime_type: str = "image/png") -> str:
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{b64}"


def _download_video(url: str) -> tuple[bytes, str]:
    with httpx.Client(timeout=120.0, follow_redirects=True) as h:
        r = h.get(url)
        r.raise_for_status()
        ct = (r.headers.get("content-type") or "video/mp4").split(";")[0].strip()
        return r.content, ct


def generate_video_runway_gen4_text(
    prompt_text: str,
    *,
    model: str | None = None,
    duration: int = 5,
    ratio: TextToVideoRatio = "1280:720",
    seed: Optional[int] = None,
    poll_timeout_seconds: float = 900.0,
    on_progress: Optional[VideoProgressCallback] = None,
) -> RunwayGen4VideoResult:
    """
    Text-to-video (Gen-4 family). Default ``gen4.5``; ``duration`` 2–10 seconds.
    """
    pt = prompt_text.strip()
    if not pt:
        raise ValueError("prompt_text must be non-empty")
    if duration < 2 or duration > 10:
        raise ValueError("duration must be between 2 and 10 seconds")

    mid = (model or DEFAULT_TEXT_MODEL).strip()
    if mid != "gen4.5":
        raise ValueError(
            f"text-to-video in this module is wired for gen4.5; got {mid!r}. "
            "Set RUNWAY_TEXT_TO_VIDEO_MODEL=gen4.5 or extend runway_gen4.py for Veo models."
        )

    client = _client()
    emit_video_progress(on_progress, "submitted", model=mid, mode="text_to_video")

    kwargs: dict = {
        "model": "gen4.5",
        "prompt_text": pt,
        "duration": duration,
        "ratio": ratio,
    }
    if seed is not None:
        kwargs["seed"] = seed

    task = client.text_to_video.create(**kwargs)
    emit_video_progress(on_progress, "generating", task_id=task.id, model=mid)

    try:
        done = task.wait_for_task_output(timeout=poll_timeout_seconds)
    except TaskFailedError as e:
        raise RuntimeError(f"Runway task failed: {e}") from e
    except TaskTimeoutError as e:
        raise RuntimeError(f"Runway task timed out: {e}") from e

    if not isinstance(done, Succeeded):
        raise RuntimeError(f"Runway unexpected status: {getattr(done, 'status', done)}")
    urls = list(done.output)
    if not urls:
        raise RuntimeError("Runway returned no output URLs")

    emit_video_progress(on_progress, "downloading", url=urls[0][:80] + "...")
    data, mime = _download_video(urls[0])

    return RunwayGen4VideoResult(
        video_bytes=data,
        mime_type=mime,
        model=mid,
        task_id=done.id,
        output_url=urls[0],
    )


def generate_video_runway_gen4_image(
    prompt_text: str,
    prompt_image: str,
    *,
    model: str | None = None,
    duration: int = 5,
    ratio: ImageToVideoRatio = "1280:720",
    seed: Optional[int] = None,
    poll_timeout_seconds: float = 900.0,
    on_progress: Optional[VideoProgressCallback] = None,
) -> RunwayGen4VideoResult:
    """
    Image-to-video. ``prompt_image`` is an HTTPS URL or data URI (see ``image_bytes_to_data_uri``).
    """
    pt = prompt_text.strip()
    pi = prompt_image.strip()
    if not pi:
        raise ValueError("prompt_image must be non-empty")
    if duration < 2 or duration > 10:
        raise ValueError("duration must be between 2 and 10 seconds")

    mid = (model or DEFAULT_IMAGE_MODEL).strip()
    if mid != "gen4.5":
        raise ValueError(
            f"image-to-video in this module is wired for gen4.5; got {mid!r}. "
            "Set RUNWAY_IMAGE_TO_VIDEO_MODEL=gen4.5 or extend runway_gen4.py."
        )

    client = _client()
    emit_video_progress(on_progress, "submitted", model=mid, mode="image_to_video")

    kwargs: dict = {
        "model": "gen4.5",
        "prompt_image": pi,
        "prompt_text": pt or "Subtle natural motion, cinematic camera, high quality.",
        "duration": duration,
        "ratio": ratio,
    }
    if seed is not None:
        kwargs["seed"] = seed

    task = client.image_to_video.create(**kwargs)
    emit_video_progress(on_progress, "generating", task_id=task.id, model=mid)

    try:
        done = task.wait_for_task_output(timeout=poll_timeout_seconds)
    except TaskFailedError as e:
        raise RuntimeError(f"Runway task failed: {e}") from e
    except TaskTimeoutError as e:
        raise RuntimeError(f"Runway task timed out: {e}") from e

    if not isinstance(done, Succeeded):
        raise RuntimeError(f"Runway unexpected status: {getattr(done, 'status', done)}")
    urls = list(done.output)
    if not urls:
        raise RuntimeError("Runway returned no output URLs")

    emit_video_progress(on_progress, "downloading", url=urls[0][:80] + "...")
    data, mime = _download_video(urls[0])

    return RunwayGen4VideoResult(
        video_bytes=data,
        mime_type=mime,
        model=mid,
        task_id=done.id,
        output_url=urls[0],
    )
