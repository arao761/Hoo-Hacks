"""ElevenLabs Eleven Music — text-to-song with vocals + instrumentation (REST).

Environment:
  ELEVENLABS_API_KEY  (required; alias: ELEVEN_API_KEY)
  Optional: ELEVENLABS_MUSIC_MODEL (default: music_v1)
  Optional: ELEVENLABS_MUSIC_LENGTH_MS (default: 90000 — 90s, max 600000)
  Optional: ELEVENLABS_MUSIC_OUTPUT_FORMAT (default: mp3_44100_128)

Docs: https://elevenlabs.io/docs/api-reference/music/stream
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx

from progress_events import MusicProgressCallback, emit_music_progress

MUSIC_STREAM_URL = "https://api.elevenlabs.io/v1/music/stream"
DEFAULT_MODEL = os.environ.get("ELEVENLABS_MUSIC_MODEL", "music_v1").strip()
DEFAULT_LENGTH_MS = int(os.environ.get("ELEVENLABS_MUSIC_LENGTH_MS", "90000"))
DEFAULT_OUTPUT_FORMAT = os.environ.get("ELEVENLABS_MUSIC_OUTPUT_FORMAT", "mp3_44100_128").strip()


@dataclass(frozen=True)
class ElevenMusicResult:
    audio_bytes: bytes
    mime_type: str
    model: str


def _api_key() -> str:
    key = (
        os.environ.get("ELEVENLABS_API_KEY", "").strip()
        or os.environ.get("ELEVEN_API_KEY", "").strip()
    )
    if not key:
        raise RuntimeError(
            "ElevenLabs API key missing: set ELEVENLABS_API_KEY (or ELEVEN_API_KEY) in "
            "Ai Integrations/.env — no quotes around the value."
        )
    return key


def _clamp_length_ms(ms: int) -> int:
    return max(3_000, min(600_000, ms))


def generate_music_elevenlabs(
    prompt: str,
    *,
    force_instrumental: bool = False,
    music_length_ms: Optional[int] = None,
    model_id: Optional[str] = None,
    output_format: Optional[str] = None,
    timeout_seconds: float = 600.0,
    on_progress: Optional[MusicProgressCallback] = None,
) -> ElevenMusicResult:
    """
    Full-track generation (vocals + instruments) unless ``force_instrumental`` is True.

    ``prompt`` is the full creative brief (genre, mood, lyrics / theme — describe what
    the singer should convey).
    """
    p = prompt.strip()
    if not p:
        raise ValueError("prompt must be non-empty")

    mid = (model_id or DEFAULT_MODEL).strip()
    fmt = (output_format or DEFAULT_OUTPUT_FORMAT).strip()
    length = _clamp_length_ms(music_length_ms if music_length_ms is not None else DEFAULT_LENGTH_MS)

    emit_music_progress(
        on_progress,
        "prompted",
        model=mid,
        prompt_chars=len(p),
        force_instrumental=force_instrumental,
    )

    body: dict = {
        "prompt": p,
        "model_id": mid,
        "music_length_ms": length,
    }
    if force_instrumental:
        body["force_instrumental"] = True

    headers = {
        "xi-api-key": _api_key(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    params = {"output_format": fmt}

    emit_music_progress(
        on_progress,
        "generating",
        model=mid,
        endpoint="api.elevenlabs.io/v1/music/stream",
    )

    with httpx.Client(timeout=timeout_seconds) as client:
        r = client.post(
            MUSIC_STREAM_URL,
            params=params,
            headers=headers,
            json=body,
        )

    if r.status_code >= 400:
        detail: str
        try:
            j = r.json()
            detail = str(j.get("detail", j))
        except Exception:
            detail = (r.text or "")[:800]
        if r.status_code == 402:
            raise RuntimeError(
                "ElevenLabs returned 402 Payment Required — your key works, but this account "
                "does not have billing/credits or access to Eleven Music. "
                "Open https://elevenlabs.io/ → Pricing / Subscription and confirm Music is included. "
                f"Detail: {detail}"
            )
        raise RuntimeError(
            f"ElevenLabs music API HTTP {r.status_code}: {detail}"
        )

    data = r.content

    emit_music_progress(
        on_progress,
        "decoding",
        model=mid,
        bytes=len(data),
    )

    mime = "audio/mpeg"
    if fmt.startswith("mp3"):
        mime = "audio/mpeg"
    elif "pcm" in fmt or "wav" in fmt:
        mime = "audio/wav"

    return ElevenMusicResult(audio_bytes=data, mime_type=mime, model=mid)
