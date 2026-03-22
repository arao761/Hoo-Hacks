"""LearnLens music generation: Vertex Lyria 2 (instrumental) or ElevenLabs Music (vocals + bed)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

from elevenlabs_music import generate_music_elevenlabs
from lyria_vertex import LyriaMusicResult, generate_music_vertex
from progress_events import MusicProgressCallback, emit_music_progress

MusicProvider = Literal["vertex", "elevenlabs"]


@dataclass(frozen=True)
class MusicGenerationOutput:
    audio_bytes: bytes
    mime_type: str
    provider: MusicProvider
    model: str
    """Additional clips if sample_count > 1 (Lyria only)."""
    all_clips: tuple[bytes, ...]


def _resolve_provider(explicit: Optional[str]) -> MusicProvider:
    raw = (explicit or os.environ.get("LEARNLENS_MUSIC_PROVIDER", "vertex")).strip().lower()
    if raw in ("vertex", "lyria", "google"):
        return "vertex"
    if raw in ("elevenlabs", "eleven", "11labs"):
        return "elevenlabs"
    raise ValueError(
        f"Unknown LEARNLENS_MUSIC_PROVIDER={raw!r}; use 'vertex' (Lyria) or 'elevenlabs' (Eleven Music)"
    )


def _prompt_with_negative(base: str, negative_prompt: Optional[str]) -> str:
    if not negative_prompt or not negative_prompt.strip():
        return base
    return f"{base.strip()}\n\nAvoid or exclude: {negative_prompt.strip()}"


def generate_learnlens_music(
    prompt: str,
    *,
    provider: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    sample_count: int = 1,
    force_instrumental: bool = False,
    on_progress: Optional[MusicProgressCallback] = None,
    emit_generation_done: bool = True,
) -> MusicGenerationOutput:
    """
    Generate music from a text prompt.

    - **vertex**: Lyria ``lyria-002``, instrumental WAV (~30s). ``seed`` / ``sample_count`` apply.
    - **elevenlabs**: Eleven Music, MP3 by default; includes **vocals + instruments** unless
      ``force_instrumental`` is True. ``seed`` / ``sample_count`` are ignored.

    When building lesson audio in ``music_pipeline``, use ``emit_generation_done=False`` so the
    terminal ``done`` fires after mixing/upload.
    """
    which = _resolve_provider(provider)

    if which == "vertex":
        if seed is not None and sample_count > 1:
            raise ValueError("Lyria API: use either seed or sample_count>1, not both")
        result: LyriaMusicResult = generate_music_vertex(
            prompt.strip(),
            negative_prompt=negative_prompt,
            seed=seed,
            sample_count=sample_count,
            on_progress=on_progress,
        )
        if emit_generation_done:
            total = sum(len(b) for b in result.samples)
            emit_music_progress(
                on_progress,
                "done",
                stage="audio_ready",
                model=result.model,
                mime_type=result.mime_type,
                clip_count=len(result.samples),
                primary_bytes=len(result.audio_bytes),
                total_bytes=total,
            )
        return MusicGenerationOutput(
            audio_bytes=result.audio_bytes,
            mime_type=result.mime_type,
            provider="vertex",
            model=result.model,
            all_clips=result.samples,
        )

    # elevenlabs — single prompt field; fold negative prompt into text
    el = generate_music_elevenlabs(
        _prompt_with_negative(prompt, negative_prompt),
        force_instrumental=force_instrumental,
        on_progress=on_progress,
    )
    if emit_generation_done:
        emit_music_progress(
            on_progress,
            "done",
            stage="audio_ready",
            model=el.model,
            mime_type=el.mime_type,
            clip_count=1,
            primary_bytes=len(el.audio_bytes),
            total_bytes=len(el.audio_bytes),
        )
    return MusicGenerationOutput(
        audio_bytes=el.audio_bytes,
        mime_type=el.mime_type,
        provider="elevenlabs",
        model=el.model,
        all_clips=(el.audio_bytes,),
    )
