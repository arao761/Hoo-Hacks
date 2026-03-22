"""LearnLens video generation entrypoint (Runway Gen-4 or ElevenLabs slideshow + TTS)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Sequence, Union, cast

from progress_events import VideoProgressCallback, emit_video_progress
from runway_gen4 import (
    ImageToVideoRatio,
    RunwayGen4VideoResult,
    TextToVideoRatio,
    generate_video_runway_gen4_image,
    generate_video_runway_gen4_text,
    image_bytes_to_data_uri,
)

_TEXT_RATIOS = frozenset({"1280:720", "720:1280"})
_IMAGE_RATIOS = frozenset(
    {"1280:720", "720:1280", "1104:832", "960:960", "832:1104", "1584:672"}
)


def _text_ratio(r: Optional[str]) -> TextToVideoRatio:
    v = (r or "1280:720").strip()
    if v not in _TEXT_RATIOS:
        raise ValueError(f"text-to-video ratio must be one of {sorted(_TEXT_RATIOS)}")
    return cast(TextToVideoRatio, v)


def _image_ratio(r: Optional[str]) -> ImageToVideoRatio:
    v = (r or "1280:720").strip()
    if v not in _IMAGE_RATIOS:
        raise ValueError(f"image-to-video ratio must be one of {sorted(_IMAGE_RATIOS)}")
    return cast(ImageToVideoRatio, v)

VideoProvider = Literal["runway", "elevenlabs_slideshow"]


@dataclass(frozen=True)
class VideoGenerationOutput:
    video_bytes: bytes
    mime_type: str
    provider: VideoProvider
    model: str
    task_id: str
    output_url: str


def _resolve_provider(explicit: Optional[str]) -> VideoProvider:
    raw = (explicit or os.environ.get("LEARNLENS_VIDEO_PROVIDER", "runway")).strip().lower()
    if raw in ("runway", "runwayml", "gen4"):
        return "runway"
    if raw in ("elevenlabs_slideshow", "elevenlabs", "slideshow", "eleven"):
        return "elevenlabs_slideshow"
    raise ValueError(
        f"Unknown LEARNLENS_VIDEO_PROVIDER={raw!r}; use 'runway' or 'elevenlabs_slideshow'"
    )


def generate_learnlens_video(
    prompt_text: str,
    *,
    provider: Optional[str] = None,
    prompt_image: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/png",
    duration_seconds: int = 5,
    ratio: Optional[str] = None,
    seed: Optional[int] = None,
    poll_timeout_seconds: float = 900.0,
    on_progress: Optional[VideoProgressCallback] = None,
    emit_generation_done: bool = True,
    slideshow_image_paths: Optional[Sequence[Union[str, Path]]] = None,
    slideshow_width: int = 1280,
    slideshow_height: int = 720,
    elevenlabs_voice_id: Optional[str] = None,
) -> VideoGenerationOutput:
    """
    Generate a short video. Without ``prompt_image`` / ``image_bytes``, uses **text-to-video**
    (``gen4.5``). With an image source, uses **image-to-video**.

    ``prompt_image`` may be an HTTPS URL or a data URI; ``image_bytes`` is wrapped as a data URI.

    When ``provider`` is ``elevenlabs_slideshow`` (or ``LEARNLENS_VIDEO_PROVIDER`` is set
    accordingly), ``prompt_text`` is the **narration script**, and ``slideshow_image_paths``
    must list at least one local image. That path uses ElevenLabs TTS plus FFmpeg (still frames),
    not generative motion video.
    """
    which = _resolve_provider(provider)
    if which == "elevenlabs_slideshow":
        from elevenlabs_slideshow_video import build_elevenlabs_slideshow_mp4_bytes

        if not slideshow_image_paths:
            raise ValueError(
                "elevenlabs_slideshow requires slideshow_image_paths with at least one image file"
            )
        resolved = [Path(p).expanduser().resolve() for p in slideshow_image_paths]
        for p in resolved:
            if not p.is_file():
                raise FileNotFoundError(p)

        model = os.environ.get("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2").strip()
        emit_video_progress(
            on_progress,
            "submitted",
            provider="elevenlabs_slideshow",
            slides=len(resolved),
            prompt_chars=len(prompt_text or ""),
        )
        video_bytes = build_elevenlabs_slideshow_mp4_bytes(
            resolved,
            prompt_text,
            width=slideshow_width,
            height=slideshow_height,
            voice_id=elevenlabs_voice_id,
            on_progress=on_progress,
        )
        if emit_generation_done:
            emit_video_progress(
                on_progress,
                "done",
                stage="video_ready",
                model=model,
                task_id="elevenlabs-slideshow",
                mime_type="video/mp4",
                bytes=len(video_bytes),
            )
        return VideoGenerationOutput(
            video_bytes=video_bytes,
            mime_type="video/mp4",
            provider="elevenlabs_slideshow",
            model=model,
            task_id="elevenlabs-slideshow",
            output_url="",
        )

    result: RunwayGen4VideoResult
    if image_bytes is not None:
        uri = image_bytes_to_data_uri(image_bytes, image_mime)
        result = generate_video_runway_gen4_image(
            prompt_text,
            uri,
            duration=duration_seconds,
            ratio=_image_ratio(ratio),
            seed=seed,
            poll_timeout_seconds=poll_timeout_seconds,
            on_progress=on_progress,
        )
    elif prompt_image and prompt_image.strip():
        result = generate_video_runway_gen4_image(
            prompt_text,
            prompt_image.strip(),
            duration=duration_seconds,
            ratio=_image_ratio(ratio),
            seed=seed,
            poll_timeout_seconds=poll_timeout_seconds,
            on_progress=on_progress,
        )
    else:
        result = generate_video_runway_gen4_text(
            prompt_text,
            duration=duration_seconds,
            ratio=_text_ratio(ratio),
            seed=seed,
            poll_timeout_seconds=poll_timeout_seconds,
            on_progress=on_progress,
        )

    if emit_generation_done:
        emit_video_progress(
            on_progress,
            "done",
            stage="video_ready",
            model=result.model,
            task_id=result.task_id,
            mime_type=result.mime_type,
            bytes=len(result.video_bytes),
        )

    return VideoGenerationOutput(
        video_bytes=result.video_bytes,
        mime_type=result.mime_type,
        provider="runway",
        model=result.model,
        task_id=result.task_id,
        output_url=result.output_url,
    )
