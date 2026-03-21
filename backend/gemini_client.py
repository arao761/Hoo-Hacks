# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/gemini_client.py
# python
from typing import Dict, Any

from models import OutputType


def expand_topic_with_gemini(topic: str, output_type: OutputType) -> Dict[str, Any]:
    """
    Person 2 responsibility: define structured prompts.
    Actual call to Gemini can be filled in later or by AI integrations.
    """
    if output_type is OutputType.image:
        return {
            "type": "image",
            "visual_description": f"Detailed educational illustration about {topic}",
            "pedagogy_notes": "Explain concept with labels, arrows, and simple language.",
        }

    if output_type is OutputType.song:
        return {
            "type": "song",
            "style": "uplifting educational jingle",
            "mood": "encouraging, clear",
            "lyrics_brief": f"Explain {topic} in simple terms with a chorus summarizing the key idea.",
        }

    # video
    return {
        "type": "video",
        "scenes": [
            {
                "title": f"Intro to {topic}",
                "visual": f"High-level overview of {topic}",
                "narration": f"Short explanation introducing {topic}.",
            },
            {
                "title": f"Core concept of {topic}",
                "visual": f"Step-by-step explanation of how {topic} works.",
                "narration": f"Deeper explanation of the main mechanisms behind {topic}.",
            },
        ],
        "style": "concise 5–10s educational explainer",
    }