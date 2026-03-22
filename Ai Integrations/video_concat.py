"""Concatenate MP4 clips with FFmpeg (stream copy or re-encode).

Requires ``ffmpeg`` on PATH (e.g. ``brew install ffmpeg``).

Clips from the same Runway settings usually share codec/resolution; ``try_copy_then_reencode``
uses ``-c copy`` first (fast, lossless) and falls back to H.264/AAC if that fails.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Sequence


def _require_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install it (e.g. brew install ffmpeg) to merge clips."
        )
    return exe


def _run_ffmpeg(args: list[str], *, cwd: str | None = None) -> None:
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {err[-2000:]}")


def concat_mp4_files(
    clip_paths: Sequence[Path],
    output_path: Path,
    *,
    strategy: Literal["try_copy_then_reencode", "copy", "reencode"] = "try_copy_then_reencode",
    video_only: bool = False,
) -> Path:
    """
    Concatenate MP4 files in order into ``output_path``.

    Uses a concat demuxer list in a temp directory (clips referenced by basename).
    """
    paths = [Path(p).expanduser().resolve() for p in clip_paths]
    if len(paths) < 1:
        raise ValueError("need at least one clip")
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(p)

    ffmpeg = _require_ffmpeg()
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="learnlens_concat_") as td:
        td_path = Path(td)
        staged: list[Path] = []
        for i, src in enumerate(paths):
            dest = td_path / f"clip_{i:04d}.mp4"
            dest.write_bytes(src.read_bytes())
            staged.append(dest)

        list_file = td_path / "concat_list.txt"
        lines = [f"file '{p.name}'" for p in staged]
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        def run_copy() -> None:
            _run_ffmpeg(
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
                    str(list_file),
                    "-c",
                    "copy",
                    str(output_path),
                ],
                cwd=str(td_path),
            )

        def run_reencode() -> None:
            cmd = [
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
                str(list_file),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-movflags",
                "+faststart",
            ]
            if video_only:
                cmd.append("-an")
            else:
                cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            cmd.append(str(output_path))
            _run_ffmpeg(cmd, cwd=str(td_path))

        if strategy == "copy":
            run_copy()
        elif strategy == "reencode":
            run_reencode()
        else:
            try:
                run_copy()
            except RuntimeError:
                run_reencode()

    return output_path


def concat_mp4_bytes(
    clips: Sequence[bytes],
    output_path: Path,
    *,
    strategy: Literal["try_copy_then_reencode", "copy", "reencode"] = "try_copy_then_reencode",
    video_only: bool = False,
) -> Path:
    """Write each blob to a temp file, then :func:`concat_mp4_files`."""
    if len(clips) < 1:
        raise ValueError("need at least one clip")
    with tempfile.TemporaryDirectory(prefix="learnlens_clipbytes_") as td:
        td_path = Path(td)
        paths: list[Path] = []
        for i, data in enumerate(clips):
            p = td_path / f"part_{i:04d}.mp4"
            p.write_bytes(data)
            paths.append(p)
        return concat_mp4_files(
            paths,
            output_path,
            strategy=strategy,
            video_only=video_only,
        )
