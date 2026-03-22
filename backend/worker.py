# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/worker.py
# python
import logging
import asyncio
import sys
import os
import time
import io
import math
import struct
import subprocess
import tempfile
import textwrap
import wave
from typing import Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Ai Integrations"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from models import OutputMetadata, OutputStatus, OutputType
from redis_client import dequeue_job, save_output_metadata
from gemini_client import expand_topic_with_gemini
from infra import upload_media, publish_progress

# Maps output_type string to MIME type for upload_media
MEDIA_CONTENT_TYPES = {
    "image": "image/png",
    "song":  "audio/wav",
    "video": "video/mp4",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("learnlens-worker")


def _generate_placeholder_song_wav(topic: str, duration_seconds: float = 6.0) -> bytes:
    """
    Return a small valid WAV so the frontend audio player can actually play output.
    This is a fallback until the real music provider is fully wired into backend worker.
    """
    sample_rate = 44100
    channels = 1
    sample_width = 2  # 16-bit PCM
    total_frames = int(sample_rate * duration_seconds)

    # Vary pitch slightly by topic length so every request is not identical.
    base_freq = 220.0 + (len(topic) % 8) * 22.0
    amplitude = 0.25

    with io.BytesIO() as buf:
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)

            frames = bytearray()
            for i in range(total_frames):
                t = i / sample_rate
                # Simple two-tone educational jingle-like beep.
                tone = math.sin(2 * math.pi * base_freq * t) + 0.5 * math.sin(2 * math.pi * (base_freq * 1.5) * t)
                sample = int(max(-1.0, min(1.0, tone * amplitude)) * 32767)
                frames.extend(struct.pack("<h", sample))

            wav_file.writeframes(bytes(frames))

        return buf.getvalue()


def _generate_placeholder_image_png() -> bytes:
    """Generate a simple valid PNG image using ffmpeg."""
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, "placeholder.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=1024x576:r=1",
            "-frames:v",
            "1",
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        with open(out_path, "rb") as f:
            return f.read()


def _generate_colored_placeholder_png(color: str) -> bytes:
    """Generate a solid-color PNG for slideshow fallback frames."""
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, "slide.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=1024x576:d=1",
            "-frames:v",
            "1",
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        with open(out_path, "rb") as f:
            return f.read()


def _generate_text_slide_png(title: str, body: str, color: str) -> bytes:
    """Render a readable educational slide using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size=size)
                except Exception:
                    continue
        return ImageFont.load_default()

    img = Image.new("RGB", (1280, 720), color=color)
    draw = ImageDraw.Draw(img)

    title_font = _load_font(64)
    body_font = _load_font(38)

    title_text = (title or "Lesson").strip()
    body_text = textwrap.fill((body or "Let's learn this concept together.").strip(), width=44)

    # Draw a soft panel behind text to keep readability high across colors.
    panel_margin = 60
    panel_top = 80
    panel_bottom = 640
    draw.rounded_rectangle(
        [panel_margin, panel_top, 1280 - panel_margin, panel_bottom],
        radius=28,
        fill=(0, 0, 0, 180),
    )

    draw.text((100, 130), title_text, fill=(255, 255, 255), font=title_font)
    draw.text((100, 260), body_text, fill=(240, 240, 240), font=body_font, spacing=12)

    with io.BytesIO() as buf:
        img.save(buf, format="PNG")
        return buf.getvalue()


def _generate_placeholder_video_mp4() -> bytes:
    """Generate a short valid MP4 clip using ffmpeg."""
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, "placeholder.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=navy:s=1280x720:d=3",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=3",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        with open(out_path, "rb") as f:
            return f.read()


def _build_image_prompt(topic: str, prompt_struct: dict) -> str:
    visual = str(prompt_struct.get("visual_description", "")).strip()
    notes = str(prompt_struct.get("pedagogy_notes", "")).strip()
    parts = [f"Educational illustration about: {topic}"]
    if visual:
        parts.append(f"Visual direction: {visual}")
    if notes:
        parts.append(f"Teaching notes: {notes}")
    return "\n".join(parts)


def _build_video_prompt(topic: str, prompt_struct: dict) -> str:
    style = str(prompt_struct.get("style", "educational explainer")).strip()
    scenes = prompt_struct.get("scenes") or []
    parts = [f"Create a short educational video about: {topic}", f"Style: {style}"]
    if isinstance(scenes, list):
        for i, scene in enumerate(scenes[:3], start=1):
            if isinstance(scene, dict):
                title = str(scene.get("title", "")).strip()
                visual = str(scene.get("visual", "")).strip()
                narration = str(scene.get("narration", "")).strip()
                parts.append(f"Scene {i}: {title}")
                if visual:
                    parts.append(f"- Visual: {visual}")
                if narration:
                    parts.append(f"- Narration: {narration}")
    return "\n".join(parts)


def _build_video_narration(topic: str, prompt_struct: dict) -> str:
    """Build plain narration text instead of instruction-style generation prompts."""
    scenes = prompt_struct.get("scenes") or []
    narration_chunks = []

    if isinstance(scenes, list):
        for scene in scenes[:5]:
            if not isinstance(scene, dict):
                continue
            narration = str(scene.get("narration", "")).strip()
            if narration:
                narration_chunks.append(narration)

    if narration_chunks:
        return f"Today we are learning about {topic}. " + " ".join(narration_chunks)

    return (
        f"Today we are learning about {topic}. "
        f"In this lesson, we explore the key ideas clearly with simple examples and a short recap."
    )


def _build_slideshow_slides(prompt_struct: dict) -> list[tuple[str, str, str]]:
    scenes = prompt_struct.get("scenes") or []
    palette = ["#204c63", "#2f6b3f", "#5b4a87", "#7a4d2b"]
    slides: list[tuple[str, str, str]] = []

    if isinstance(scenes, list):
        for i, scene in enumerate(scenes[:4]):
            if not isinstance(scene, dict):
                continue
            title = str(scene.get("title", "")).strip() or f"Key Idea {i + 1}"
            visual = str(scene.get("visual", "")).strip()
            narration = str(scene.get("narration", "")).strip()
            body = narration or visual or "A focused explanation of this part of the lesson."
            slides.append((title, body, palette[i % len(palette)]))

    if not slides:
        slides = [
            ("Introduction", "We begin with the main idea and why it matters.", palette[0]),
            ("How It Works", "Step by step, we break down the core mechanism.", palette[1]),
            ("Summary", "Quick recap of the most important points.", palette[2]),
        ]

    return slides


def _build_song_prompt(topic: str, prompt_struct: dict) -> str:
    lyrics_brief = str(prompt_struct.get("lyrics_brief", "")).strip()
    style = str(prompt_struct.get("style", "educational song")).strip()
    mood = str(prompt_struct.get("mood", "clear and engaging")).strip()

    parts = [
        f"Create a short educational song about: {topic}",
        f"Style: {style}",
        f"Mood: {mood}",
    ]
    if lyrics_brief:
        parts.append(f"Lyrics direction: {lyrics_brief}")

    return "\n".join(parts)


def _generate_song_audio(topic: str, prompt_struct: dict) -> Tuple[bytes, str, str]:
    """
    Generate song audio via Person 3 pipeline when available.
    Falls back to placeholder WAV if provider call fails.
    Returns: (audio_bytes, mime_type, provider_name)
    """
    provider = (os.getenv("LEARNLENS_MUSIC_PROVIDER", "").strip().lower() or None)
    if provider is None and os.getenv("ELEVENLABS_API_KEY", "").strip():
        provider = "elevenlabs"

    try:
        prompt = _build_song_prompt(topic, prompt_struct)

        # Prefer ElevenLabs direct path so song generation works even when Vertex
        # dependencies are not installed in the backend runtime env.
        if provider in (None, "elevenlabs"):
            from elevenlabs_music import generate_music_elevenlabs

            el = generate_music_elevenlabs(prompt)
            return el.audio_bytes, el.mime_type, "elevenlabs"

        # Vertex/other providers: use Person 3 unified router.
        from music_generation import generate_learnlens_music

        result = generate_learnlens_music(prompt, provider=provider)
        return result.audio_bytes, result.mime_type, result.provider
    except Exception as exc:  # noqa: BLE001
        logger.warning("Real song generation failed (%s); using placeholder WAV fallback.", exc)
        return _generate_placeholder_song_wav(topic), "audio/wav", "fallback"


def _generate_image_media(topic: str, prompt_struct: dict) -> Tuple[bytes, str, str]:
    provider = (os.getenv("LEARNLENS_IMAGE_PROVIDER", "").strip().lower() or None)
    try:
        from image_generation import generate_learnlens_image

        result = generate_learnlens_image(_build_image_prompt(topic, prompt_struct), provider=provider)
        return result.image_bytes, result.mime_type, result.provider
    except Exception as exc:  # noqa: BLE001
        logger.warning("Real image generation failed (%s); using placeholder PNG fallback.", exc)
        return _generate_placeholder_image_png(), "image/png", "fallback"


def _generate_video_media(topic: str, prompt_struct: dict) -> Tuple[bytes, str, str]:
    provider = (os.getenv("LEARNLENS_VIDEO_PROVIDER", "").strip().lower() or None)
    try:
        from video_generation import generate_learnlens_video

        prompt = _build_video_prompt(topic, prompt_struct)
        narration_text = _build_video_narration(topic, prompt_struct)

        # ElevenLabs slideshow requires at least one local image path.
        if provider == "elevenlabs_slideshow":
            with tempfile.TemporaryDirectory() as td:
                slide_paths = []
                for i, (title, body, color) in enumerate(_build_slideshow_slides(prompt_struct), start=1):
                    slide_path = os.path.join(td, f"slide_{i}.png")
                    with open(slide_path, "wb") as f:
                        try:
                            f.write(_generate_text_slide_png(title, body, color))
                        except Exception:
                            # Keep video generation resilient if ffmpeg drawtext is unavailable.
                            f.write(_generate_colored_placeholder_png(color))
                    slide_paths.append(slide_path)

                result = generate_learnlens_video(
                    narration_text,
                    provider=provider,
                    slideshow_image_paths=slide_paths,
                )
        else:
            result = generate_learnlens_video(prompt, provider=provider)

        return result.video_bytes, result.mime_type, result.provider
    except Exception as exc:  # noqa: BLE001
        logger.warning("Real video generation failed (%s); using placeholder MP4 fallback.", exc)
        return _generate_placeholder_video_mp4(), "video/mp4", "fallback"


def process_job(job: dict) -> None:
    job_id = job["job_id"]
    topic = job["topic"]
    output_type_str = job["output_type"]
    output_type = OutputType(output_type_str)

    logger.info("Processing job %s - %s (%s)", job_id, topic, output_type_str)

    # mark as processing
    meta = OutputMetadata(
        job_id=job_id,
        topic=topic,
        output_type=output_type,
        status=OutputStatus.processing,
    )
    save_output_metadata(meta)

    try:
        # 1) Prompt expansion via Gemini
        asyncio.run(publish_progress(job_id, "prompted", "Building your prompt..."))
        prompt_struct = expand_topic_with_gemini(topic, output_type)

        # 2) Call media generation
        asyncio.run(publish_progress(job_id, "generating", f"Generating your {output_type_str}..."))

        if output_type is OutputType.song:
            generated_bytes, content_type, song_provider = _generate_song_audio(topic, prompt_struct)
            meta.extra = {"prompt": prompt_struct, "song_provider": song_provider}
        elif output_type is OutputType.image:
            generated_bytes, content_type, image_provider = _generate_image_media(topic, prompt_struct)
            meta.extra = {"prompt": prompt_struct, "image_provider": image_provider}
        elif output_type is OutputType.video:
            generated_bytes, content_type, video_provider = _generate_video_media(topic, prompt_struct)
            meta.extra = {"prompt": prompt_struct, "video_provider": video_provider}
        else:
            generated_bytes = str(prompt_struct).encode("utf-8")
            content_type = MEDIA_CONTENT_TYPES.get(output_type_str, "application/octet-stream")

        # 3) Upload to S3 via infra
        asyncio.run(publish_progress(job_id, "uploading", "Almost there..."))
        cdn_url = upload_media(generated_bytes, content_type, job_id)

        # 4) Save final metadata
        meta.status = OutputStatus.done
        meta.cdn_url = cdn_url
        if not meta.extra:
            meta.extra = {"prompt": prompt_struct}
        save_output_metadata(meta)

        asyncio.run(publish_progress(job_id, "done", "Ready!", {"cdn_url": cdn_url}))
        logger.info("Job %s completed: %s", job_id, cdn_url)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed", job_id)
        meta.status = OutputStatus.error
        meta.error_message = str(exc)
        save_output_metadata(meta)
        asyncio.run(publish_progress(job_id, "error", str(exc)))


def run_worker_loop(poll_interval: int = 1) -> None:
    logger.info("Worker started, waiting for jobs...")
    while True:
        job = dequeue_job(block=True, timeout=5)
        if not job:
            time.sleep(poll_interval)
            continue

        process_job(job)


if __name__ == "__main__":
    run_worker_loop()