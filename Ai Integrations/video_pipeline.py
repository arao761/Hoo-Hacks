"""Runway Gen-4 → video bytes → optional storage handoff."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

from progress_events import VideoProgressCallback, emit_video_progress
from storage_handoff import StoredVideoRef, VideoStorageSink
from video_generation import VideoGenerationOutput, generate_learnlens_video


@dataclass(frozen=True)
class VideoPipelineResult:
    generation: VideoGenerationOutput
    stored: Optional[StoredVideoRef]


def generate_learnlens_video_and_store(
    prompt_text: str,
    storage: VideoStorageSink,
    *,
    prompt_image: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/png",
    provider: Optional[str] = None,
    duration_seconds: int = 5,
    ratio: Optional[str] = None,
    seed: Optional[int] = None,
    basename_hint: str = "learnlens",
    on_progress: Optional[VideoProgressCallback] = None,
    slideshow_image_paths: Optional[Sequence[Union[str, Path]]] = None,
    slideshow_width: int = 1280,
    slideshow_height: int = 720,
    elevenlabs_voice_id: Optional[str] = None,
) -> VideoPipelineResult:
    """Generate video (Runway or ElevenLabs slideshow), upload bytes, emit ``uploading`` then ``done``."""
    gen = generate_learnlens_video(
        prompt_text,
        provider=provider,
        prompt_image=prompt_image,
        image_bytes=image_bytes,
        image_mime=image_mime,
        duration_seconds=duration_seconds,
        ratio=ratio,
        seed=seed,
        on_progress=on_progress,
        emit_generation_done=False,
        slideshow_image_paths=slideshow_image_paths,
        slideshow_width=slideshow_width,
        slideshow_height=slideshow_height,
        elevenlabs_voice_id=elevenlabs_voice_id,
    )

    emit_video_progress(
        on_progress,
        "uploading",
        basename_hint=basename_hint,
        bytes=len(gen.video_bytes),
        mime_type=gen.mime_type,
    )
    ref = storage.store_video(
        data=gen.video_bytes,
        content_type=gen.mime_type,
        basename_hint=basename_hint,
    )
    emit_video_progress(
        on_progress,
        "done",
        stage="stored",
        object_key=ref.object_key,
        url=ref.url,
        mime_type=ref.content_type,
        task_id=gen.task_id,
    )
    return VideoPipelineResult(generation=gen, stored=ref)
