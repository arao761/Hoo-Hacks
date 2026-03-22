import json
import logging
import os
from typing import Any, Dict

from models import OutputType

logger = logging.getLogger("learnlens-gemini")

# ---------------------------------------------------------------------------
# Gemini / Vertex AI call
# ---------------------------------------------------------------------------

_SONG_SYSTEM = """You are an expert educational content creator who specialises in music-based learning.
Given a topic, return ONLY a JSON object (no markdown fences) with these keys:
- style: a detailed music style description suitable for an AI music generator (instruments, tempo, genre, energy)
- mood: emotional tone of the song
- lyrics_brief: 3-4 sentences of concrete lyrics content — key facts, a memorable chorus hook, and a closing line
- music_prompt: a single richly-detailed paragraph (80-120 words) written as a direct instruction to an AI music model; include instruments, tempo BPM estimate, genre, and educational feel
"""

_VIDEO_SYSTEM = """You are an expert scriptwriter for short educational explainer videos.
Given a topic, return ONLY a JSON object (no markdown fences) with these keys:
- style: visual/narrative style (e.g. "animated explainer with warm colours")
- scenes: array of exactly 4 scene objects, each with:
    - title: short scene heading (5 words max)
    - visual: one sentence describing what is shown on screen
    - narration: 2-3 natural, conversational sentences of spoken narration for that scene (good for text-to-speech)
- full_narration: a single flowing 150-200 word narration script that covers the whole topic engagingly, written for text-to-speech delivery
"""

_SONG_USER = "Topic: {topic}\n\nGenerate a rich, engaging educational song structure for this topic."
_VIDEO_USER = "Topic: {topic}\n\nGenerate a compelling educational video script for this topic."


def _call_gemini(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Call Gemini 2.0 Flash via the REST API directly using httpx."""
    import httpx

    api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.7},
    }

    resp = httpx.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown fences if the model wrapped the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ---------------------------------------------------------------------------
# Rich fallback templates (used when Gemini is unavailable)
# ---------------------------------------------------------------------------

def _song_fallback(topic: str) -> Dict[str, Any]:
    return {
        "type": "song",
        "style": (
            "upbeat acoustic-pop educational song with piano, light percussion, and warm acoustic guitar. "
            "Moderate tempo around 110 BPM. Bright and encouraging energy."
        ),
        "mood": "enthusiastic, clear, and memorable",
        "lyrics_brief": (
            f"Verse 1 introduces what {topic} is and why it matters. "
            f"The pre-chorus builds curiosity with a question about {topic}. "
            f"The chorus repeats the single most important fact about {topic} as a catchy hook. "
            f"Verse 2 dives into how {topic} works step by step. "
            f"Outro reinforces the key takeaway with an encouraging closing line."
        ),
        "music_prompt": (
            f"An upbeat, engaging educational song about {topic}. "
            f"Acoustic guitar and piano lead with light hand percussion. "
            f"Tempo: 110 BPM. Genre: educational acoustic-pop. "
            f"Warm, encouraging vocal style. The melody is simple and memorable so "
            f"students can easily recall the key facts about {topic}. "
            f"Bright major key. Builds energy from verse to chorus, then resolves warmly."
        ),
    }


def _video_fallback(topic: str) -> Dict[str, Any]:
    return {
        "type": "video",
        "style": "friendly animated explainer with clear narration and warm colour palette",
        "scenes": [
            {
                "title": f"What is {topic}?",
                "visual": f"Bold title card with the words '{topic}' and a simple illustrative icon.",
                "narration": (
                    f"Have you ever wondered about {topic}? "
                    f"Today we're going to break it down in a way that's simple, clear, and easy to remember."
                ),
            },
            {
                "title": "Why It Matters",
                "visual": f"Animated diagram showing the real-world impact of {topic}.",
                "narration": (
                    f"Understanding {topic} is important because it shapes the world around us every day. "
                    f"Whether you're a student or just curious, knowing this concept opens up a whole new way of seeing things."
                ),
            },
            {
                "title": "How It Works",
                "visual": f"Step-by-step animated breakdown of the core mechanism behind {topic}.",
                "narration": (
                    f"At its core, {topic} works through a specific process. "
                    f"Let's walk through it step by step so the key ideas really stick."
                ),
            },
            {
                "title": "Quick Recap",
                "visual": "Three bullet-point summary cards appearing one by one.",
                "narration": (
                    f"So to recap: {topic} is a foundational concept with real-world relevance. "
                    f"Now that you know the key ideas, you're ready to explore even further. Keep it up!"
                ),
            },
        ],
        "full_narration": (
            f"Welcome! Today's lesson is all about {topic}. "
            f"This is one of those topics that once you understand it, you start seeing it everywhere. "
            f"Let's start with the basics. {topic} refers to a core idea or process that plays an important role "
            f"in this subject area. It influences how things work and why certain outcomes happen the way they do. "
            f"Now let's look at the mechanics. The key thing to understand is that {topic} follows a clear and "
            f"logical structure. When you break it down step by step, each part builds on the last. "
            f"This makes it much easier to remember and apply. "
            f"Here's something worth noting: many students find {topic} tricky at first, but once the core idea clicks, "
            f"everything else follows naturally. Focus on the fundamentals and you'll be well on your way. "
            f"To wrap up, {topic} is a powerful concept that rewards careful study. "
            f"Great work today — keep exploring!"
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def expand_topic_with_gemini(topic: str, output_type: OutputType) -> Dict[str, Any]:
    """
    Use Gemini to generate a rich structured prompt for song or video generation.
    Falls back to improved static templates if Gemini is unavailable.
    """
    if output_type is OutputType.song:
        try:
            result = _call_gemini(
                _SONG_SYSTEM,
                _SONG_USER.format(topic=topic),
            )
            result["type"] = "song"
            logger.info("Gemini song prompt generated for: %s", topic)
            return result
        except Exception as exc:
            logger.warning("Gemini unavailable for song prompt (%s); using fallback.", exc)
            return _song_fallback(topic)

    # video
    try:
        result = _call_gemini(
            _VIDEO_SYSTEM,
            _VIDEO_USER.format(topic=topic),
        )
        result["type"] = "video"
        logger.info("Gemini video prompt generated for: %s", topic)
        return result
    except Exception as exc:
        logger.warning("Gemini unavailable for video prompt (%s); using fallback.", exc)
        return _video_fallback(topic)
