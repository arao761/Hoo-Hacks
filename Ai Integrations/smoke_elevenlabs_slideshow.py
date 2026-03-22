#!/usr/bin/env python3
"""
ElevenLabs narration + image slideshow → one MP4 (FFmpeg).

Requires ELEVENLABS_API_KEY, ffmpeg/ffprobe, and (for ``--images``) real image files.
Optional: ``ELEVENLABS_TTS_VOICE_ID``; if unset, the premade Rachel voice is used.

  cd "Ai Integrations"
  python smoke_elevenlabs_slideshow.py --demo \\
    --narration "First idea. Second idea." -o lesson.mp4 -v

  # Or use your own files (paths must exist):
  python smoke_elevenlabs_slideshow.py --images ./photo1.png ./photo2.png \\
    --narration "Hello." -o lesson.mp4 -v
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv


def _ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        print("ffmpeg not found on PATH (needed for --demo and for building the MP4).", file=sys.stderr)
        sys.exit(1)
    return exe


def _write_demo_slide_pngs(out_dir: Path) -> list[Path]:
    """Two solid-color 1280×720 PNGs via lavfi (no extra Python deps)."""
    ffmpeg = _ffmpeg_exe()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("coral", "_learnlens_demo_slide_0.png"),
        ("steelblue", "_learnlens_demo_slide_1.png"),
    ]
    paths: list[Path] = []
    for color, name in specs:
        p = out_dir / name
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=1280x720",
            "-frames:v",
            "1",
            str(p),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            print(f"ffmpeg demo image failed: {err[-500:]}", file=sys.stderr)
            sys.exit(1)
        paths.append(p)
    return paths


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")

    try:
        from video_generation import generate_learnlens_video
    except ImportError:
        print("Run from the Ai Integrations directory.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="ElevenLabs TTS + slideshow MP4 smoke test")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--images",
        nargs="+",
        type=Path,
        help="One or more PNG/JPEG paths that exist on disk (order = slide order)",
    )
    src.add_argument(
        "--demo",
        action="store_true",
        help="Create two placeholder PNGs with ffmpeg and use those (no image files needed)",
    )
    parser.add_argument(
        "--narration",
        required=True,
        help="Spoken script (ElevenLabs TTS)",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("learnlens_smoke_eleven_slideshow.mp4"),
        help="Output MP4 path",
    )
    parser.add_argument(
        "--voice-id",
        default=None,
        help="Override ELEVENLABS_TTS_VOICE_ID",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.demo:
        with tempfile.TemporaryDirectory(prefix="learnlens_slideshow_demo_") as td:
            image_paths = _write_demo_slide_pngs(Path(td))
            return _run_slideshow(
                image_paths,
                args,
                load_generate=generate_learnlens_video,
            )

    assert args.images is not None
    image_paths = [p.expanduser() for p in args.images]
    missing = [p for p in image_paths if not p.is_file()]
    if missing:
        for p in missing:
            print(f"Image not found: {p.resolve()}", file=sys.stderr)
        print(
            "Use real paths to PNG/JPEG files, or run with --demo to auto-create placeholders.",
            file=sys.stderr,
        )
        return 1

    return _run_slideshow(
        [p.resolve() for p in image_paths],
        args,
        load_generate=generate_learnlens_video,
    )


def _run_slideshow(
    image_paths: list[Path],
    args: argparse.Namespace,
    *,
    load_generate,
) -> int:
    generate_learnlens_video = load_generate

    def on_progress(phase: str, payload: dict) -> None:
        if args.verbose:
            print(f"[{phase}] {payload}", file=sys.stderr)

    out = Path(args.out).expanduser().resolve()
    result = generate_learnlens_video(
        args.narration.strip(),
        provider="elevenlabs_slideshow",
        slideshow_image_paths=image_paths,
        elevenlabs_voice_id=args.voice_id,
        on_progress=on_progress,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result.video_bytes)
    if args.verbose:
        print(f"Wrote {out} ({len(result.video_bytes)} bytes)", file=sys.stderr)
    else:
        print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
