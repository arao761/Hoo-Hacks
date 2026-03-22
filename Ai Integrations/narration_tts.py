"""Concept narration via Google Cloud Text-to-Speech (LINEAR16 WAV).

Lyria outputs instrumental audio only; this layer speaks the lesson script so learners
hear explanations over the bed track.

Environment (optional):
  GOOGLE_TTS_VOICE — e.g. en-US-Neural2-J, en-US-Neural2-F (default: en-US-Neural2-J)

Requires Cloud Text-to-Speech API enabled on the GCP project; uses Application Default Credentials.
"""

from __future__ import annotations

import io
import os
import wave
from typing import Optional

from google.cloud import texttospeech_v1 as texttospeech

DEFAULT_VOICE = os.environ.get("GOOGLE_TTS_VOICE", "en-US-Neural2-J")
DEFAULT_SAMPLE_RATE = 48_000


def synthesize_narration_wav(
    text: str,
    *,
    language_code: str = "en-US",
    voice_name: Optional[str] = None,
    speaking_rate: float = 1.0,
    sample_rate_hz: int = DEFAULT_SAMPLE_RATE,
) -> bytes:
    """
    Return a mono 16-bit PCM WAV containing the spoken ``text``.

    ``sample_rate_hz`` should match the instrumental bed (Lyria uses 48000 Hz).
    """
    t = text.strip()
    if not t:
        raise ValueError("narration text must be non-empty")

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=t)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=(voice_name or DEFAULT_VOICE).strip(),
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=int(sample_rate_hz),
        speaking_rate=float(speaking_rate),
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    raw = response.audio_content
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate_hz))
        wf.writeframes(raw)
    return bio.getvalue()
