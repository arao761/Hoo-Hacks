"""Build a lesson-style MP4: still images (slideshow) + ElevenLabs TTS narration (FFmpeg).

ElevenLabs does not offer a public Runway-style generative motion-video API; this path
produces a real MP4 by timing each slide to the narration length and muxing AAC audio.

Requires ``ffmpeg`` and ``ffprobe`` on PATH (e.g. ``brew install ffmpeg``).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Optional, Sequence

from elevenlabs_tts import text_to_speech_mp3
from progress_events import VideoProgressCallback, emit_video_progress
from video_concat import concat_mp4_files


def _require_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install it (e.g. brew install ffmpeg) for slideshow video."
        )
    return exe


def _require_ffprobe() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError(
            "ffprobe not found on PATH. Install ffmpeg (includes ffprobe), e.g. brew install ffmpeg."
        )
    return exe


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"command failed (exit {proc.returncode}): {' '.join(cmd[:4])}… — {err[-2000:]}")


def audio_duration_seconds(audio_path: Path) -> float:
    ffprobe = _require_ffprobe()
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "ffprobe failed").strip())
    raw = (proc.stdout or "").strip()
    if not raw:
        raise RuntimeError("ffprobe returned no duration")
    line = raw.splitlines()[0]
    return float(line)


def _encode_still_clip(
    image_path: Path,
    duration_sec: float,
    out_mp4: Path,
    *,
    width: int,
    height: int,
) -> None:
    ffmpeg = _require_ffmpeg()
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-vf",
            vf,
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-t",
            f"{duration_sec:.6f}",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(out_mp4),
        ]
    )


def _mux_video_and_audio(video_mp4: Path, audio_path: Path, out_mp4: Path) -> None:
    ffmpeg = _require_ffmpeg()
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_mp4),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out_mp4),
        ]
    )


def build_elevenlabs_slideshow_mp4_bytes(
    image_paths: Sequence[Path],
    narration_text: str,
    *,
    width: int = 1280,
    height: int = 720,
    voice_id: Optional[str] = None,
    tts_timeout_seconds: float = 600.0,
    concat_strategy: Literal["try_copy_then_reencode", "copy", "reencode"] = "reencode",
    on_progress: Optional[VideoProgressCallback] = None,
) -> bytes:
    """
    Synthesize narration with ElevenLabs TTS, split duration across ``image_paths`` evenly,
    encode one H.264 clip per image, concat, then mux the full narration MP3.
    """
    paths = [Path(p).expanduser().resolve() for p in image_paths]
    if not paths:
        raise ValueError("need at least one image path")
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(p)

    emit_video_progress(on_progress, "generating", stage="elevenlabs_tts", bytes=0)
    mp3_bytes = text_to_speech_mp3(
        narration_text, voice_id=voice_id, timeout_seconds=tts_timeout_seconds
    )

    with tempfile.TemporaryDirectory(prefix="learnlens_slideshow_") as td:
        td_path = Path(td)
        audio_path = td_path / "narration.mp3"
        audio_path.write_bytes(mp3_bytes)
        total_dur = audio_duration_seconds(audio_path)
        n = len(paths)
        base = total_dur / n
        # Last segment absorbs float remainder so sum matches total_dur
        durations = [base] * n
        if n > 0:
            durations[-1] = max(0.01, total_dur - base * (n - 1))

        emit_video_progress(
            on_progress,
            "merging",
            stage="encode_slides",
            slide_count=n,
            duration_sec=total_dur,
        )
        segments: list[Path] = []
        for i, img in enumerate(paths):
            seg = td_path / f"slide_{i:04d}.mp4"
            _encode_still_clip(img, durations[i], seg, width=width, height=height)
            segments.append(seg)

        silent = td_path / "video_noaudio.mp4"
        concat_mp4_files(segments, silent, strategy=concat_strategy, video_only=True)

        emit_video_progress(on_progress, "merging", stage="mux_audio", clip_count=len(segments))
        final_mp4 = td_path / "lesson.mp4"
        _mux_video_and_audio(silent, audio_path, final_mp4)
        return final_mp4.read_bytes()
