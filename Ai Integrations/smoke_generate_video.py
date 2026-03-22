#!/usr/bin/env python3
"""
Runway Gen-4 video smoke test (text-to-video or image-to-video).

Requires RUNWAYML_API_SECRET in ``Ai Integrations/.env``.

  cd "Ai Integrations"

  # Text-only (gen4.5)
  python smoke_generate_video.py --prompt "Calm educational animation of a plant cell, soft lighting" -o clip.mp4 -v

  # Image URL (still image → motion)
  python smoke_generate_video.py --image-url "https://example.com/frame.png" \\
    --prompt "Slow pan across the scene, subtle parallax" -o clip.mp4

  # Local PNG/JPEG
  python smoke_generate_video.py --image ./keyframe.png --prompt "Gentle zoom in" -o clip.mp4
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")

    try:
        from video_generation import generate_learnlens_video
    except ImportError:
        print("Run from the Ai Integrations directory.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="LearnLens Runway Gen-4 video smoke test")
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--image-url",
        default=None,
        help="HTTPS URL of the start frame (image-to-video)",
    )
    src.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Local image file (PNG/JPEG) for image-to-video",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Motion / scene description (and style) for Runway",
    )
    parser.add_argument(
        "-o",
        "--out",
        default="learnlens_smoke_video.mp4",
        help="Output path (.mp4)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Clip length in seconds (2–10, default 5)",
    )
    parser.add_argument(
        "--ratio",
        default="1280:720",
        help="Aspect ratio, e.g. 1280:720 or 720:1280",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
    )
    args = parser.parse_args()

    if not (
        os.environ.get("RUNWAYML_API_SECRET", "").strip()
        or os.environ.get("RUNWAY_API_KEY", "").strip()
    ):
        print(
            "Set RUNWAYML_API_SECRET (or RUNWAY_API_KEY) in Ai Integrations/.env",
            file=sys.stderr,
        )
        return 1

    def on_progress(phase: str, detail: dict) -> None:
        if args.verbose:
            print(f"[{phase}]", detail, flush=True)

    cb = on_progress if args.verbose else None

    image_bytes = None
    image_mime = "image/png"
    prompt_image = args.image_url

    if args.image is not None:
        p = args.image.expanduser().resolve()
        if not p.is_file():
            print(f"Not a file: {p}", file=sys.stderr)
            return 1
        suffix = p.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            image_mime = "image/jpeg"
        elif suffix == ".webp":
            image_mime = "image/webp"
        image_bytes = p.read_bytes()

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = generate_learnlens_video(
            args.prompt,
            prompt_image=prompt_image,
            image_bytes=image_bytes,
            image_mime=image_mime,
            duration_seconds=args.duration,
            ratio=args.ratio,
            on_progress=cb,
        )
    except Exception as e:
        print(f"Generation failed: {e}", file=sys.stderr)
        return 1

    out.write_bytes(result.video_bytes)
    print(f"Wrote {len(result.video_bytes)} bytes ({result.mime_type}) task={result.task_id}")
    print(f"File: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
