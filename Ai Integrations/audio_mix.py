"""Mix two PCM WAV byte streams (e.g. Lyria bed + Cloud TTS voice)."""

from __future__ import annotations

import io
import wave
from typing import Final

import numpy as np

_MAX_F32: Final[float] = 1.0


def _read_wav_f32(wav_bytes: bytes) -> tuple[np.ndarray, int, int]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        sr = wf.getframerate()
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        nf = wf.getnframes()
        raw = wf.readframes(nf)
    if sw != 2:
        raise ValueError(f"only 16-bit PCM WAV supported (got sample width {sw})")
    pcm = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if nch == 1:
        pcm = pcm.reshape(-1, 1)
    else:
        pcm = pcm.reshape(-1, nch)
    return pcm, sr, nch


def _write_wav_f32(pcm: np.ndarray, sample_rate: int) -> bytes:
    if pcm.ndim != 2 or pcm.shape[1] not in (1, 2):
        raise ValueError("pcm must be shape [frames, 1] or [frames, 2]")
    clipped = np.clip(pcm, -_MAX_F32, _MAX_F32)
    pcm16 = (clipped * 32767.0).astype("<i2")
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(pcm.shape[1])
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())
    return bio.getvalue()


def _resample_f32(pcm: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return pcm
    n_src = pcm.shape[0]
    n_dst = max(1, int(round(n_src * dst_sr / src_sr)))
    x_old = np.arange(n_src, dtype=np.float64) / float(src_sr)
    t_new = np.arange(n_dst, dtype=np.float64) / float(dst_sr)
    out = np.zeros((n_dst, pcm.shape[1]), dtype=np.float32)
    for c in range(pcm.shape[1]):
        out[:, c] = np.interp(t_new, x_old, pcm[:, c].astype(np.float64)).astype(np.float32)
    return out


def _to_stereo(pcm: np.ndarray) -> np.ndarray:
    if pcm.shape[1] == 2:
        return pcm
    return np.column_stack((pcm[:, 0], pcm[:, 0]))


def _pad_end(pcm: np.ndarray, target_frames: int) -> np.ndarray:
    n = pcm.shape[0]
    if n >= target_frames:
        return pcm[:target_frames]
    pad = target_frames - n
    return np.vstack((pcm, np.zeros((pad, pcm.shape[1]), dtype=np.float32)))


def mix_wav_bytes(
    bed_wav: bytes,
    voice_wav: bytes,
    *,
    bed_gain: float = 0.2,
    voice_gain: float = 1.0,
) -> bytes:
    """
    Align sample rate (to the bed), stereo width, and length; return a stereo WAV.

    The longer of the two tracks is padded with silence on the shorter one so the
    full narration is audible under (or after) the instrumental.
    """
    bed, sr_b, _ = _read_wav_f32(bed_wav)
    voice, sr_v, _ = _read_wav_f32(voice_wav)
    voice = _resample_f32(voice, sr_v, sr_b)
    bed = _to_stereo(bed)
    voice = _to_stereo(voice)
    n = max(bed.shape[0], voice.shape[0])
    bed = _pad_end(bed, n)
    voice = _pad_end(voice, n)
    mixed = bed * float(bed_gain) + voice * float(voice_gain)
    mixed = np.clip(mixed, -_MAX_F32, _MAX_F32)
    return _write_wav_f32(mixed, sr_b)
