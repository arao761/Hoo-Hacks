#!/usr/bin/env python3
"""
Merge several Runway text-to-video clips into one lesson MP4 (FFmpeg).

Requires RUNWAYML_API_SECRET and ffmpeg on PATH (brew install ffmpeg).

  cd "Ai Integrations"

  # One prompt per line in a file
  python smoke_merge_lesson_video.py --segments-file lesson_segments.txt -o lesson_merged.mp4 -v

  # Or inline prompts
  python smoke_merge_lesson_video.py -p "Intro: friendly classroom" \\
    -p "Middle: diagram of the water cycle" \\
    -p "Outro: recap and smile" -o lesson.mp4
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
        from lesson_video_merge import generate_lesson_video_segments_and_merge
    except ImportError:
        print("Run from the Ai Integrations directory.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(
        description="Generate N Runway clips and FFmpeg-concat into one MP4",
    )
    parser.add_argument(
        "--segments-file",
        type=Path,
        default=None,
        help="Text file: one segment prompt per line",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        action="append",
        dest="prompts",
        default=[],
        help="Segment prompt (repeat -p for multiple)",
    )
    parser.add_argument(
        "-o",
        "--out",
        required=True,
        type=Path,
        help="Output merged .mp4 path",
    )
    parser.add_argument("--duration", type=int, default=5, help="Seconds per clip (2–10)")
    parser.add_argument("--ratio", default="1280:720")
    parser.add_argument(
        "--concat",
        choices=("try_copy_then_reencode", "copy", "reencode"),
        default="try_copy_then_reencode",
    )
    parser.add_argument(
        "--video-only-audio-strip",
        action="store_true",
        help="If concat fails on audio, retry logic uses video_only in re-encode; "
        "or pass this to strip audio in re-encode path only",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if not (
        os.environ.get("RUNWAYML_API_SECRET", "").strip()
        or os.environ.get("RUNWAY_API_KEY", "").strip()
    ):
        print("Set RUNWAYML_API_SECRET in .env", file=sys.stderr)
        return 1

    lines: list[str] = []
    if args.segments_file is not None:
        p = args.segments_file.expanduser().resolve()
        if not p.is_file():
            print(f"Not a file: {p}", file=sys.stderr)
            return 1
        lines = p.read_text(encoding="utf-8").splitlines()
    lines.extend(args.prompts or [])
    if not any(x.strip() for x in lines):
        print("Provide --segments-file and/or -p prompts.", file=sys.stderr)
        return 1

    def on_progress(phase: str, detail: dict) -> None:
        if args.verbose:
            print(f"[{phase}]", detail, flush=True)

    try:
        result = generate_lesson_video_segments_and_merge(
            lines,
            output_path=args.out,
            duration_seconds=args.duration,
            ratio=args.ratio,
            concat_strategy=args.concat,  # type: ignore[arg-type]
            video_only_concat=args.video_only_audio_strip,
            on_progress=on_progress if args.verbose else None,
        )
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)
        return 1

    print(f"Merged {len(result.segments)} clips → {len(result.merged_bytes)} bytes")
    print(f"File: {result.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
