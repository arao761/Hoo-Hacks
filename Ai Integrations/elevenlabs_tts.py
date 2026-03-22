"""ElevenLabs Text-to-Speech (REST) — narration audio as MP3 bytes.

Environment:
  ELEVENLABS_API_KEY (required; alias: ELEVEN_API_KEY)
  ELEVENLABS_TTS_VOICE_ID (optional; defaults to premade "Rachel" for all accounts)
  Optional: ELEVENLABS_TTS_MODEL (default: eleven_multilingual_v2)
  Optional: ELEVENLABS_TTS_OUTPUT_FORMAT (default: mp3_44100_128)

Override ``voice_id=`` in code, or set ``ELEVENLABS_TTS_VOICE_ID``, to use another voice from the dashboard.

Docs: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Sequence

import httpx

# Premade "Rachel" (multilingual narration) — works on any ElevenLabs account without cloning.
DEFAULT_PREMADE_TTS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# ElevenLabs per-request limits vary by tier; chunk below this and concat with ffmpeg.
MAX_SINGLE_TTS_CHARS = 3800


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


def _default_voice_id(explicit: Optional[str]) -> str:
    vid = (explicit or os.environ.get("ELEVENLABS_TTS_VOICE_ID", "")).strip()
    return vid or DEFAULT_PREMADE_TTS_VOICE_ID


def _split_for_tts(text: str, max_chars: int) -> list[str]:
    t = text.strip()
    if len(t) <= max_chars:
        return [t]
    sentences = re.split(r"(?<=[.!?])\s+", t)
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        candidate = f"{cur} {s}".strip() if cur else s
        if len(candidate) <= max_chars:
            cur = candidate
            continue
        if cur:
            chunks.append(cur)
        if len(s) <= max_chars:
            cur = s
        else:
            for i in range(0, len(s), max_chars):
                part = s[i : i + max_chars].strip()
                if part:
                    chunks.append(part)
            cur = ""
    if cur:
        chunks.append(cur)
    return chunks


def _concat_mp3_with_ffmpeg(part_paths: Sequence[Path], out_mp3: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg not found on PATH; required to join long TTS into one MP3. "
            "Install ffmpeg (e.g. brew install ffmpeg)."
        )
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="learnlens_tts_concat_") as td:
        list_f = Path(td) / "audio_list.txt"
        lines = "\n".join(f"file '{p.resolve().as_posix()}'" for p in part_paths) + "\n"
        list_f.write_text(lines, encoding="utf-8")
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_f),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128k",
                str(out_mp3),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(f"ffmpeg MP3 concat failed: {err[-1500:]}")


def _tts_single_request(
    text: str,
    *,
    voice_id: Optional[str],
    model_id: Optional[str],
    output_format: Optional[str],
    timeout_seconds: float,
) -> bytes:
    vid = _default_voice_id(voice_id)
    model = (model_id or os.environ.get("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")).strip()
    fmt = (
        output_format or os.environ.get("ELEVENLABS_TTS_OUTPUT_FORMAT", "mp3_44100_128")
    ).strip()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    headers = {
        "xi-api-key": _api_key(),
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {"text": text, "model_id": model}
    params = {"output_format": fmt}
    with httpx.Client(timeout=timeout_seconds) as client:
        r = client.post(url, headers=headers, json=payload, params=params)
        r.raise_for_status()
        return r.content


def text_to_speech_mp3(
    text: str,
    *,
    voice_id: Optional[str] = None,
    model_id: Optional[str] = None,
    output_format: Optional[str] = None,
    timeout_seconds: float = 120.0,
) -> bytes:
    """
    Convert ``text`` to MP3 bytes via ``POST /v1/text-to-speech/{voice_id}``.

    Long scripts are split under ~3800 characters, synthesized per chunk, then merged with ffmpeg.
    """
    t = (text or "").strip()
    if not t:
        raise ValueError("text must be non-empty for TTS")

    if len(t) <= MAX_SINGLE_TTS_CHARS:
        return _tts_single_request(
            t,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
            timeout_seconds=timeout_seconds,
        )

    parts = _split_for_tts(t, MAX_SINGLE_TTS_CHARS)
    with tempfile.TemporaryDirectory(prefix="learnlens_tts_parts_") as td:
        td_path = Path(td)
        paths: list[Path] = []
        per = max(timeout_seconds, 180.0)
        for i, chunk in enumerate(parts):
            p = td_path / f"narr_{i:03d}.mp3"
            p.write_bytes(
                _tts_single_request(
                    chunk,
                    voice_id=voice_id,
                    model_id=model_id,
                    output_format=output_format,
                    timeout_seconds=per,
                )
            )
            paths.append(p)
        merged = td_path / "narration_merged.mp3"
        _concat_mp3_with_ffmpeg(paths, merged)
        return merged.read_bytes()
