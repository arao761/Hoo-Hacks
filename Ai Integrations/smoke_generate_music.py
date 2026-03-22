#!/usr/bin/env python3
"""
Lesson / music smoke test.

- **vertex** (default or ``LEARNLENS_MUSIC_PROVIDER=vertex``): Lyria bed + Google Cloud TTS → mixed WAV.
- **elevenlabs**: Eleven Music → vocal + instruments (typical **MP3**); ``--narration`` becomes lyrical / teaching content in the prompt.

Uses ``Ai Integrations/.env``. Images are unchanged (still Vertex elsewhere in the repo).

  cd "Ai Integrations"

  # Eleven Music (vocals + song) — set ELEVENLABS_API_KEY and e.g. LEARNLENS_MUSIC_PROVIDER=elevenlabs
  python smoke_generate_music.py --provider elevenlabs --style educational_jingle -o lesson.mp3 -v

  # Vertex + TTS (mixed WAV)
  python smoke_generate_music.py --provider vertex --style science_explorer -o lesson.wav -v
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_PROMPT = (
    "Educational upbeat jingle, major key, acoustic guitar and soft piano, "
    "clear melody suitable for learning content, instrumental only, 90 bpm"
)

DEFAULT_NARRATION = (
    "Welcome to this quick concept clip. Photosynthesis is how plants turn sunlight into sugar, "
    "using water from the soil and carbon dioxide from the air. "
    "The chloroplasts inside leaves capture light energy to fuel that process."
)


def _resolved_provider(arg_provider: str | None) -> str:
    if arg_provider:
        return arg_provider.strip().lower()
    return os.environ.get("LEARNLENS_MUSIC_PROVIDER", "vertex").strip().lower()


def _normalize_out_path(path: Path, provider: str) -> Path:
    """Use .mp3 default extension for Eleven when user left .wav from Vertex habits."""
    if provider == "elevenlabs" and path.suffix.lower() == ".wav":
        return path.with_suffix(".mp3")
    return path


def main() -> int:
    _env_file = Path(__file__).resolve().parent / ".env"
    _loaded = load_dotenv(_env_file)

    try:
        from music_generation import generate_learnlens_music
        from music_pipeline import generate_learnlens_lesson_audio
        from music_style_presets import (
            CORE_STYLE_SLUGS,
            INSTRUMENTAL_NEGATIVE,
            LEARNING_CONCEPT_STYLE_SLUGS,
            STYLE_PRESET_SLUGS,
            adapt_style_prompt_for_eleven_music,
            get_style_prompt,
        )
    except ImportError:
        print("Run from the Ai Integrations directory.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(
        description="LearnLens music smoke: Vertex (Lyria+TTS) or ElevenLabs (Eleven Music)",
    )
    parser.add_argument(
        "-o",
        "--out",
        default="learnlens_smoke_music.wav",
        help="Output path (.mp3 recommended for elevenlabs)",
    )
    parser.add_argument(
        "--provider",
        choices=("vertex", "elevenlabs"),
        default=None,
        help="Override LEARNLENS_MUSIC_PROVIDER for this run",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--style",
        choices=STYLE_PRESET_SLUGS,
        default=None,
        metavar="PRESET",
        help="Single curated genre preset",
    )
    mode.add_argument(
        "--all-styles",
        action="store_true",
        help="Run every preset in STYLE_PRESETS",
    )
    mode.add_argument(
        "--suite",
        choices=("core", "learning", "all"),
        default=None,
        help="Batch: core (3 demos), learning (concept-focused genres), or all presets",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Custom music prompt (only when no --style / --suite / --all-styles)",
    )
    parser.add_argument(
        "--narration",
        default=DEFAULT_NARRATION,
        help="Vertex: TTS script. ElevenLabs: teaching content / lyrical theme woven into the song.",
    )
    parser.add_argument(
        "--instrumental-only",
        action="store_true",
        help="Music only: Lyria WAV (vertex) or force_instrumental (elevenlabs)",
    )
    parser.add_argument(
        "--bed-gain",
        type=float,
        default=0.2,
        help="Vertex mix only: bed level (default 0.2)",
    )
    parser.add_argument(
        "--voice-gain",
        type=float,
        default=1.0,
        help="Vertex mix only: narration level (default 1.0)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print progress events",
    )
    args = parser.parse_args()

    prov = _resolved_provider(args.provider)
    if prov == "elevenlabs" and not (
        os.environ.get("ELEVENLABS_API_KEY", "").strip()
        or os.environ.get("ELEVEN_API_KEY", "").strip()
    ):
        print(
            "ElevenLabs: API key not loaded.\n"
            f"  Look for: {_env_file} (exists={_env_file.is_file()}, dotenv_ok={_loaded})\n"
            "  Add: ELEVENLABS_API_KEY=your_key_here\n"
            "  (same folder as smoke_generate_music.py; no spaces around =)",
            file=sys.stderr,
        )
        return 1

    def on_progress(phase: str, detail: dict) -> None:
        if args.verbose:
            print(f"[{phase}]", detail, flush=True)

    cb = on_progress if args.verbose else None

    def run_one(
        positive: str,
        negative: str | None,
        out_path: Path,
        narration: str,
    ) -> int:
        out_path = _normalize_out_path(out_path.expanduser().resolve(), prov)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if args.instrumental_only:
                result = generate_learnlens_music(
                    positive,
                    provider=prov,
                    negative_prompt=negative,
                    force_instrumental=(prov == "elevenlabs"),
                    on_progress=cb,
                )
                out_path.write_bytes(result.audio_bytes)
                label = "instrumental"
                if prov == "elevenlabs":
                    label = "Eleven Music (instrumental)"
                print(
                    f"Wrote {len(result.audio_bytes)} bytes ({result.mime_type}) "
                    f"model={result.model} provider={prov} [{label}]"
                )
            else:
                lesson = generate_learnlens_lesson_audio(
                    positive,
                    narration.strip(),
                    provider=prov,
                    negative_prompt=negative,
                    on_progress=cb,
                    bed_gain=args.bed_gain,
                    voice_gain=args.voice_gain,
                )
                out_path.write_bytes(lesson.final_audio_bytes)
                mode = "Eleven Music vocal song" if prov == "elevenlabs" else "mixed Lyria + Cloud TTS"
                print(
                    f"Wrote {len(lesson.final_audio_bytes)} bytes "
                    f"({lesson.final_content_type}) model={lesson.music.model} "
                    f"provider={prov} [{mode}]"
                )
        except Exception as e:
            print(f"Generation failed: {e}", file=sys.stderr)
            if prov == "elevenlabs":
                if "402" in str(e) or "Payment Required" in str(e):
                    print(
                        "\nHTTP 402: Eleven Music needs a paid tier or credits — "
                        "see elevenlabs.io subscription/billing. "
                        "Use --provider vertex for Lyria+TTS without Eleven Music.",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "\nCheck: ELEVENLABS_API_KEY; Eleven Music on your plan.",
                        file=sys.stderr,
                    )
            else:
                print(
                    "\nCheck: Vertex AI + Lyria; Cloud Text-to-Speech API; ADC; GOOGLE_CLOUD_PROJECT.",
                    file=sys.stderr,
                )
            return 1
        print(f"File: {out_path}")
        return 0

    narr = args.narration or ""
    if not args.instrumental_only and not narr.strip():
        print("--narration must be non-empty (or use --instrumental-only).", file=sys.stderr)
        return 1

    def style_pair(slug: str) -> tuple[str, str | None]:
        pos, neg = get_style_prompt(slug)
        if prov == "elevenlabs":
            return adapt_style_prompt_for_eleven_music(pos, neg)
        return pos, neg

    if args.all_styles:
        slugs: tuple[str, ...] = STYLE_PRESET_SLUGS
    elif args.suite == "core":
        slugs = CORE_STYLE_SLUGS
    elif args.suite == "learning":
        slugs = LEARNING_CONCEPT_STYLE_SLUGS
    elif args.suite == "all":
        slugs = STYLE_PRESET_SLUGS
    elif args.style:
        pos, neg = style_pair(args.style)
        return run_one(pos, neg, Path(args.out), narr)
    else:
        if args.prompt is None:
            prompt = DEFAULT_PROMPT
            neg = INSTRUMENTAL_NEGATIVE
            if prov == "elevenlabs":
                prompt, neg = adapt_style_prompt_for_eleven_music(prompt, neg)
        else:
            prompt = args.prompt
            neg = None
        return run_one(prompt, neg, Path(args.out), narr)

    base = Path(args.out).expanduser().resolve()
    base = _normalize_out_path(base, prov)
    stem, suf = base.stem, base.suffix
    if not suf:
        suf = ".mp3" if prov == "elevenlabs" else ".wav"
    parent = base.parent
    rc = 0
    for slug in slugs:
        pos, neg = style_pair(slug)
        target = parent / f"{stem}_{slug}{suf}"
        print(f"\n=== {slug} -> {target.name} ===", flush=True)
        r = run_one(pos, neg, target, narr)
        if r != 0:
            rc = r
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
