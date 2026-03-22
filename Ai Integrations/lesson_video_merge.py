"""Multi-segment Runway clips → one lesson MP4 via FFmpeg concat."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from progress_events import VideoProgressCallback, emit_video_progress
from video_concat import concat_mp4_bytes
from video_generation import VideoGenerationOutput, generate_learnlens_video


@dataclass(frozen=True)
class MergedLessonVideoResult:
    """One merged file plus per-segment Runway outputs (for debugging or re-merge)."""

    merged_bytes: bytes
    mime_type: str
    segments: tuple[VideoGenerationOutput, ...]
    """Written merged file when ``output_path`` was provided to the generator."""
    output_path: Optional[Path]


def generate_lesson_video_segments_and_merge(
    segment_prompts: list[str],
    *,
    output_path: Path,
    duration_seconds: int = 5,
    ratio: Optional[str] = None,
    provider: Optional[str] = None,
    poll_timeout_seconds: float = 900.0,
    concat_strategy: Literal["try_copy_then_reencode", "copy", "reencode"] = "try_copy_then_reencode",
    video_only_concat: bool = False,
    on_progress: Optional[VideoProgressCallback] = None,
) -> MergedLessonVideoResult:
    """
    For each non-empty line in ``segment_prompts``, run **text-to-video** (same settings),
    then **concatenate** all MP4s with FFmpeg.

    Total runtime ≈ sum of Runway jobs + one concat. Example: 6×5s clips → ~30s lesson
    (plus generation latency and API cost per segment).

    Requires **ffmpeg** on PATH.
    """
    prompts = [p.strip() for p in segment_prompts if p and p.strip()]
    if not prompts:
        raise ValueError("segment_prompts must contain at least one non-empty prompt")
    if duration_seconds < 2 or duration_seconds > 10:
        raise ValueError("duration_seconds must be between 2 and 10 for gen4.5")

    segments: list[VideoGenerationOutput] = []
    n = len(prompts)
    for i, prompt in enumerate(prompts):
        emit_video_progress(
            on_progress,
            "generating",
            segment_index=i,
            segment_total=n,
            prompt_chars=len(prompt),
        )
        seg = generate_learnlens_video(
            prompt,
            provider=provider,
            duration_seconds=duration_seconds,
            ratio=ratio,
            poll_timeout_seconds=poll_timeout_seconds,
            on_progress=on_progress,
            emit_generation_done=False,
        )
        segments.append(seg)

    emit_video_progress(
        on_progress,
        "merging",
        clip_count=len(segments),
        strategy=concat_strategy,
    )
    out = Path(output_path).expanduser().resolve()
    concat_mp4_bytes(
        [s.video_bytes for s in segments],
        out,
        strategy=concat_strategy,
        video_only=video_only_concat,
    )
    merged = out.read_bytes()
    emit_video_progress(
        on_progress,
        "done",
        stage="merged",
        bytes=len(merged),
        path=str(out),
    )
    return MergedLessonVideoResult(
        merged_bytes=merged,
        mime_type="video/mp4",
        segments=tuple(segments),
        output_path=out,
    )
