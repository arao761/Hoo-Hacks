#!/usr/bin/env python3
"""
Build a ~2–3 minute photosynthesis lesson MP4: AI slide art + ElevenLabs narration + FFmpeg.

  cd "Ai Integrations"
  # Full pipeline (Vertex Imagen or Ideogram + ElevenLabs + ffmpeg):
  python build_photosynthesis_lesson.py -o photosynthesis_lesson.mp4 -v

  # Narration + slideshow only (solid-color slides, no image API):
  python build_photosynthesis_lesson.py --demo-slides -o photosynthesis_lesson.mp4 -v

  # Vertex Imagen quota (429): slow down + retry; placeholder used for failed slides by default:
  python build_photosynthesis_lesson.py --image-delay 15 -o photosynthesis_lesson.mp4 -v

Requires: ELEVENLABS_API_KEY, ffmpeg, ffprobe.
Image APIs: LEARNLENS_IMAGE_PROVIDER=vertex (default) needs Vertex/ADC, or ideogram + its key.
"""

from __future__ import annotations

import argparse
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    from google.genai.errors import ClientError as GenaiClientError
except ImportError:
    GenaiClientError = None  # type: ignore[misc, assignment]

from dotenv import load_dotenv

# --- Lesson content: ten visuals, one continuous narration (~2.5–3 min at teaching pace) ---

SLIDE_IMAGE_PROMPTS: list[str] = [
    "Warm sunlight streaming through a lush green forest canopy, soft scientific nature illustration, "
    "no text, educational documentary mood",
    "Macro view of vibrant green leaves backlit by sun, veins visible, clean biology textbook style, no text",
    "Cross-section diagram style of a plant leaf showing internal layers and round green chloroplasts, "
    "educational illustration, soft colors, no labels or writing",
    "Abstract scientific visualization of chlorophyll molecules capturing light beams, deep greens and gold, "
    "no text or formulas",
    "Plant roots in soil drawing up water droplets toward stem, cutaway educational art style, no text",
    "Stomata on leaf surface with carbon dioxide concept as faint translucent particles in air, "
    "scientific illustration, no text",
    "Split scene sunlight on leaf and energy flowing inward as soft glow, conceptual biology art, no text",
    "Underwater scene oxygen bubbles rising from green aquatic plants in clear water, classroom demo feel, no text",
    "Healthy plant with fruit and stored energy metaphor warm sunlight, growth and sugar concept, "
    "friendly educational illustration, no text",
    "Wide landscape sun sky green fields simple food web hint plants as foundation, ecology panorama, no text",
]

NARRATION = """
Welcome to this lesson on photosynthesis — the process that keeps green plants alive and, in a very real
sense, keeps most ecosystems running.

Photosynthesis is how plants, algae, and some bacteria convert light energy into chemical energy they can
store and use. For land plants, most of the action happens in leaves, inside microscopic factories called
chloroplasts. Those chloroplasts are packed with chlorophyll, the pigment that makes leaves look green.
Chlorophyll is tuned to absorb mostly blue and red light, while more green light bounces away — which is
part of why we perceive leaves as green.

To run photosynthesis, a plant needs raw materials from its environment. It takes in carbon dioxide from
the air through tiny pores on the leaf surface called stomata. It pulls water up from the soil through
xylem tissue in roots and stems. Then, using energy from sunlight, it combines carbon dioxide and water
into sugars such as glucose. Those sugars fuel growth, repair, and reproduction — everything the plant
builds starts from energy captured in this step.

Oxygen is released along the way. That oxygen is a byproduct of splitting water during the
light-dependent reactions. It diffuses out through the same stomata and enters the atmosphere — which is
why large plant communities are so important for breathable air.

You will often see photosynthesis summarized in words as: carbon dioxide plus water, with light energy,
produces glucose and oxygen. In more advanced courses you will split the process into two cooperating
stages: the light-dependent reactions, which harvest energy and produce ATP and NADPH, and the Calvin
cycle, which uses that energy to fix carbon dioxide into sugars in a way that does not directly require
light, even though it depends on the earlier steps.

So the next time you see a leaf angled toward the sun, think of it as a small solar-powered chemical
plant — quietly turning light, air, and water into food and oxygen, supporting life far beyond the stem
it sits on.

Finally, only a slice of incoming sunlight ends up locked in sugar, but that slice is enough to anchor
food webs, crop yields, and the long-term oxygen balance that makes complex life on land possible.
Knowing how photosynthesis links sun, air, water, and sugar helps explain why forests, grasslands, and
healthy oceans matter — not only for beauty, but for the chemistry all of us depend on every day.
""".replace(
    "\n", " "
).strip()


DEMO_SLIDE_COLORS = [
    "darkseagreen",
    "steelblue",
    "goldenrod",
    "darkkhaki",
    "cadetblue",
    "slategray",
    "peru",
    "darkcyan",
    "olivedrab",
    "rosybrown",
]


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        print("ffmpeg not found on PATH.", file=sys.stderr)
        sys.exit(1)
    return exe


def write_one_demo_slide_png(out_dir: Path, index: int) -> Path:
    """Single solid-color 1280×720 PNG."""
    color = DEMO_SLIDE_COLORS[index % len(DEMO_SLIDE_COLORS)]
    ffmpeg = _ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"slide_{index:02d}.png"
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
        print((r.stderr or r.stdout or "ffmpeg failed")[-800:], file=sys.stderr)
        sys.exit(1)
    return p


def write_demo_slide_pngs(out_dir: Path, count: int) -> list[Path]:
    """Solid-color 1280×720 placeholders (one per slide)."""
    return [write_one_demo_slide_png(out_dir, i) for i in range(count)]


def _is_quota_or_rate_limit(exc: BaseException) -> bool:
    if GenaiClientError is not None and isinstance(exc, GenaiClientError):
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code == 429:
            return True
    low = str(exc).lower()
    return (
        "429" in str(exc)
        or "resource_exhausted" in low
        or "quota exceeded" in low
        or ("rate" in low and "limit" in low)
    )


def generate_slide_images_ai(
    out_dir: Path,
    *,
    verbose: bool,
    image_provider: str | None,
    image_delay_seconds: float,
    max_retries_per_slide: int,
    quota_fallback_demo: bool,
) -> list[Path]:
    from image_generation import generate_learnlens_image

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    n = len(SLIDE_IMAGE_PROMPTS)
    for i, prompt in enumerate(SLIDE_IMAGE_PROMPTS):
        if i > 0 and image_delay_seconds > 0:
            if verbose:
                print(f"[image] waiting {image_delay_seconds}s (quota pacing)…", file=sys.stderr)
            time.sleep(image_delay_seconds)

        if verbose:
            print(f"[image {i + 1}/{n}] {prompt[:72]}…", file=sys.stderr)

        last_err: BaseException | None = None
        for attempt in range(max(1, max_retries_per_slide)):
            try:
                out = generate_learnlens_image(
                    prompt,
                    provider=image_provider,
                    aspect_ratio="16:9",
                )
                suffix = ".png" if "png" in out.mime_type else ".jpg"
                p = out_dir / f"slide_{i:02d}{suffix}"
                p.write_bytes(out.image_bytes)
                paths.append(p)
                break
            except Exception as e:
                last_err = e
                if not _is_quota_or_rate_limit(e):
                    raise
                wait = min(120.0, (2**attempt) * 3.0 + random.uniform(0.0, 2.5))
                if verbose:
                    print(
                        f"[image {i + 1}/{n}] quota/rate limit (attempt {attempt + 1}/{max_retries_per_slide}), "
                        f"sleeping {wait:.1f}s…",
                        file=sys.stderr,
                    )
                time.sleep(wait)
        else:
            if quota_fallback_demo:
                print(
                    f"[image {i + 1}/{n}] still over quota after {max_retries_per_slide} tries — "
                    f"using solid-color placeholder (see --no-quota-fallback to fail instead).",
                    file=sys.stderr,
                )
                paths.append(write_one_demo_slide_png(out_dir, i))
            elif last_err is not None:
                raise last_err
            else:
                raise RuntimeError("image generation failed with no exception captured")
    return paths


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(description="Photosynthesis lesson video (slides + ElevenLabs + FFmpeg)")
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("photosynthesis_lesson.mp4"),
        help="Output MP4 path",
    )
    parser.add_argument(
        "--demo-slides",
        action="store_true",
        help="Skip image APIs; use colored placeholder slides",
    )
    parser.add_argument(
        "--image-provider",
        default=None,
        help="vertex | ideogram (default: env LEARNLENS_IMAGE_PROVIDER or vertex)",
    )
    parser.add_argument("--voice-id", default=None, help="Override ELEVENLABS_TTS_VOICE_ID")
    parser.add_argument(
        "--image-delay",
        type=float,
        default=10.0,
        metavar="SEC",
        help="Seconds to wait between image API calls (eases Vertex per-minute Imagen quotas; default: 10)",
    )
    parser.add_argument(
        "--image-retries",
        type=int,
        default=8,
        metavar="N",
        help="Retries per slide on 429 / quota (exponential backoff; default: 8)",
    )
    parser.add_argument(
        "--no-quota-fallback",
        action="store_true",
        help="Abort if a slide still hits quota after retries (default: use solid-color placeholder for that slide)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    try:
        from elevenlabs_slideshow_video import build_elevenlabs_slideshow_mp4_bytes
    except ImportError:
        print("Run from the Ai Integrations directory.", file=sys.stderr)
        return 1

    out_mp4 = Path(args.out).expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="learnlens_photo_lesson_") as td:
        work = Path(td) / "slides"
        if args.demo_slides:
            if args.verbose:
                print("[slides] demo placeholders", file=sys.stderr)
            slide_paths = write_demo_slide_pngs(work, len(SLIDE_IMAGE_PROMPTS))
        else:
            if args.verbose:
                print("[slides] generating with image API…", file=sys.stderr)
            slide_paths = generate_slide_images_ai(
                work,
                verbose=args.verbose,
                image_provider=args.image_provider,
                image_delay_seconds=args.image_delay,
                max_retries_per_slide=args.image_retries,
                quota_fallback_demo=not args.no_quota_fallback,
            )

        if args.verbose:
            wc = len(NARRATION.split())
            print(f"[narration] ~{wc} words, {len(NARRATION)} chars", file=sys.stderr)

        def on_progress(phase: str, payload: dict) -> None:
            if args.verbose:
                print(f"[{phase}] {payload}", file=sys.stderr)

        video_bytes = build_elevenlabs_slideshow_mp4_bytes(
            slide_paths,
            NARRATION,
            voice_id=args.voice_id,
            tts_timeout_seconds=600.0,
            on_progress=on_progress,
        )

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    out_mp4.write_bytes(video_bytes)
    if args.verbose:
        print(f"Wrote {out_mp4} ({len(video_bytes) // 1_048_576} MiB approx)", file=sys.stderr)
    else:
        print(str(out_mp4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
