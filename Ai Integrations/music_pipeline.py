"""Lesson audio: Vertex = Lyria bed + Cloud TTS mix; ElevenLabs = one vocal song (no separate TTS)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from audio_mix import mix_wav_bytes
from music_generation import MusicGenerationOutput, _resolve_provider, generate_learnlens_music
from narration_tts import synthesize_narration_wav
from progress_events import MusicProgressCallback, emit_music_progress
from storage_handoff import AudioStorageSink, StoredAudioRef


@dataclass(frozen=True)
class MusicPipelineResult:
    """Raw music generation plus the bytes learners play (mixed WAV or single MP3)."""

    music: MusicGenerationOutput
    final_audio_bytes: bytes
    final_content_type: str
    stored: Optional[StoredAudioRef]


def _eleven_combined_prompt(music_prompt: str, narration_text: str) -> str:
    return (
        "Educational song suitable for students. "
        f"Musical style, genre, and arrangement: {music_prompt.strip()}. "
        "The lead vocals should clearly convey this teaching content with memorable, "
        "age-appropriate lyrics: "
        f"{narration_text.strip()}"
    )


def _mixed_lesson_audio(
    music_prompt: str,
    narration_text: str,
    *,
    provider: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    sample_count: int = 1,
    on_progress: Optional[MusicProgressCallback] = None,
    bed_gain: float = 0.2,
    voice_gain: float = 1.0,
    tts_voice_name: Optional[str] = None,
    tts_speaking_rate: float = 1.0,
) -> tuple[MusicGenerationOutput, bytes]:
    nt = narration_text.strip()
    if not nt:
        raise ValueError("narration_text is required for lesson audio")

    which = _resolve_provider(provider)

    if which == "elevenlabs":
        combined = _eleven_combined_prompt(music_prompt, nt)
        gen = generate_learnlens_music(
            combined,
            provider="elevenlabs",
            negative_prompt=negative_prompt,
            seed=seed,
            sample_count=sample_count,
            force_instrumental=False,
            on_progress=on_progress,
            emit_generation_done=False,
        )
        return gen, gen.audio_bytes

    gen = generate_learnlens_music(
        music_prompt,
        provider="vertex",
        negative_prompt=negative_prompt,
        seed=seed,
        sample_count=sample_count,
        on_progress=on_progress,
        emit_generation_done=False,
    )

    emit_music_progress(
        on_progress,
        "narrating",
        chars=len(nt),
        voice=tts_voice_name or "default",
    )
    voice_wav = synthesize_narration_wav(
        nt,
        voice_name=tts_voice_name,
        speaking_rate=tts_speaking_rate,
    )

    emit_music_progress(
        on_progress,
        "mixing",
        bed_bytes=len(gen.audio_bytes),
        voice_bytes=len(voice_wav),
    )
    mixed = mix_wav_bytes(
        gen.audio_bytes,
        voice_wav,
        bed_gain=bed_gain,
        voice_gain=voice_gain,
    )
    return gen, mixed


def generate_learnlens_lesson_audio(
    music_prompt: str,
    narration_text: str,
    *,
    provider: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    sample_count: int = 1,
    on_progress: Optional[MusicProgressCallback] = None,
    bed_gain: float = 0.2,
    voice_gain: float = 1.0,
    tts_voice_name: Optional[str] = None,
    tts_speaking_rate: float = 1.0,
) -> MusicPipelineResult:
    """
    Vertex: Lyria instrumental + Cloud TTS narration → stereo WAV.

    ElevenLabs: one **vocal song** prompt (style + teaching content); returns **MP3** (typical),
    no Google TTS mixing.
    """
    gen, final_bytes = _mixed_lesson_audio(
        music_prompt,
        narration_text,
        provider=provider,
        negative_prompt=negative_prompt,
        seed=seed,
        sample_count=sample_count,
        on_progress=on_progress,
        bed_gain=bed_gain,
        voice_gain=voice_gain,
        tts_voice_name=tts_voice_name,
        tts_speaking_rate=tts_speaking_rate,
    )
    mime = gen.mime_type
    emit_music_progress(
        on_progress,
        "done",
        stage="audio_ready",
        model=gen.model,
        mime_type=mime,
        clip_count=len(gen.all_clips),
        primary_bytes=len(final_bytes),
        total_bytes=len(final_bytes),
    )
    return MusicPipelineResult(
        music=gen,
        final_audio_bytes=final_bytes,
        final_content_type=mime,
        stored=None,
    )


def generate_learnlens_lesson_audio_and_store(
    music_prompt: str,
    narration_text: str,
    storage: AudioStorageSink,
    *,
    provider: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    sample_count: int = 1,
    basename_hint: str = "learnlens",
    on_progress: Optional[MusicProgressCallback] = None,
    bed_gain: float = 0.2,
    voice_gain: float = 1.0,
    tts_voice_name: Optional[str] = None,
    tts_speaking_rate: float = 1.0,
) -> MusicPipelineResult:
    """Upload ``final_audio_bytes`` (WAV for Vertex path, MP3 typical for ElevenLabs)."""
    gen, final_bytes = _mixed_lesson_audio(
        music_prompt,
        narration_text,
        provider=provider,
        negative_prompt=negative_prompt,
        seed=seed,
        sample_count=sample_count,
        on_progress=on_progress,
        bed_gain=bed_gain,
        voice_gain=voice_gain,
        tts_voice_name=tts_voice_name,
        tts_speaking_rate=tts_speaking_rate,
    )
    mime = gen.mime_type

    emit_music_progress(
        on_progress,
        "uploading",
        basename_hint=basename_hint,
        bytes=len(final_bytes),
        mime_type=mime,
    )
    ref = storage.store_audio(
        data=final_bytes,
        content_type=mime,
        basename_hint=basename_hint,
    )
    emit_music_progress(
        on_progress,
        "done",
        stage="stored",
        object_key=ref.object_key,
        url=ref.url,
        mime_type=ref.content_type,
        model=gen.model,
        primary_bytes=len(final_bytes),
        clip_count=len(gen.all_clips),
    )
    return MusicPipelineResult(
        music=gen,
        final_audio_bytes=final_bytes,
        final_content_type=mime,
        stored=ref,
    )
