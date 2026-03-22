#!/usr/bin/env python3
"""
Generate one image and write it to disk (local smoke test).

From this directory (or with PYTHONPATH set to this directory):

  # Vertex / Imagen (ADC or service account)
  export GOOGLE_CLOUD_PROJECT=your-project
  export GOOGLE_CLOUD_LOCATION=us-central1
  export GOOGLE_GENAI_USE_VERTEXAI=True
  export LEARNLENS_IMAGE_PROVIDER=vertex
  gcloud auth application-default login   # if testing from your laptop

  python smoke_generate_image.py --preset photosynthesis --out /tmp/learnlens.png

  # Ideogram
  export LEARNLENS_IMAGE_PROVIDER=ideogram
  export IDEOGRAM_API_KEY=...

  python smoke_generate_image.py --preset black_holes --out /tmp/learnlens.png

Optional: copy .env.example to .env in this folder; the script loads it automatically.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _check_env(provider: str) -> None:
    if provider == "ideogram":
        if not os.environ.get("IDEOGRAM_API_KEY", "").strip():
            print("Missing IDEOGRAM_API_KEY.", file=sys.stderr)
            sys.exit(1)
        return
    # Vertex path (google-genai)
    missing = [k for k in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION") if not os.environ.get(k, "").strip()]
    if missing:
        print(f"Missing env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() not in ("1", "true", "yes"):
        print(
            'Set GOOGLE_GENAI_USE_VERTEXAI=True so Imagen runs on Vertex (not API-key Gemini).',
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="LearnLens image generation smoke test")
    parser.add_argument(
        "--preset",
        default="photosynthesis",
        help="Topic slug from educational_topic_presets (default: photosynthesis)",
    )
    parser.add_argument(
        "--out",
        "-o",
        default="learnlens_smoke.png",
        help="Output file path (default: learnlens_smoke.png in cwd)",
    )
    parser.add_argument(
        "--provider",
        choices=("vertex", "ideogram"),
        default=None,
        help="Override LEARNLENS_IMAGE_PROVIDER for this run",
    )
    args = parser.parse_args()

    # Load Ai Integrations/.env so you don't have to export vars every shell.
    load_dotenv(Path(__file__).resolve().parent / ".env")

    prov = (args.provider or os.environ.get("LEARNLENS_IMAGE_PROVIDER", "vertex")).strip().lower()
    if prov in ("vertex", "imagen", "vertex_imagen", "google"):
        _check_env("vertex")
    elif prov == "ideogram":
        _check_env("ideogram")

    try:
        from image_pipeline import generate_image_from_topic_preset
    except ImportError:
        print(
            "Import failed: run from the 'Ai Integrations' folder, or set:\n"
            "  export PYTHONPATH=\"/full/path/to/Hoo-Hacks/Ai Integrations\"",
            file=sys.stderr,
        )
        return 1

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = generate_image_from_topic_preset(
            args.preset,
            provider=args.provider,
        )
    except Exception as e:
        print(f"Generation failed: {e}", file=sys.stderr)
        print(
            "\nCheck env:\n"
            "  Vertex: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI=True, ADC\n"
            "  Ideogram: IDEOGRAM_API_KEY\n"
            "  LEARNLENS_IMAGE_PROVIDER=vertex|ideogram",
            file=sys.stderr,
        )
        return 1

    suffix = ".jpg" if "jpeg" in result.mime_type else ".png"
    if out_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        out_path = out_path.with_suffix(suffix)

    out_path.write_bytes(result.image_bytes)
    print(f"Wrote {len(result.image_bytes)} bytes ({result.mime_type}) via {result.provider}")
    print(f"File: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
