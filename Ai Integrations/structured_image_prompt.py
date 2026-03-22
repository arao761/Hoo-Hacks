"""Structured image prompt (e.g. from Gemini) → single string for Imagen / Ideogram."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class StructuredImagePrompt:
    """Fields your prompt-builder can populate; all model text ends up in one T2I string."""

    topic: str
    scene_description: str
    visual_style: str
    educational_framing: str = ""
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[str] = None

    def to_model_prompt(self) -> str:
        """
        Tuned for T2I: one clear scene, no on-image typography (models cannot spell).
        Teaching copy belongs in your app UI, not inside the bitmap.
        """
        topic = self.topic.strip()
        scene = self.scene_description.strip()
        style = self.visual_style.strip()
        lines = [
            "WORDLESS IMAGE: absolutely no writing anywhere in the frame — no alphabet, no digits, no symbols that look like letters.",
            "Single-panel educational illustration for students (not a comic strip, not a UI mockup, not a photo collage).",
            f"TOPIC (for your understanding only — do not write this title in the image): {topic}",
            (
                f"COMPOSITION: {scene} "
                "One focal area, generous margins, clear left-to-right or top-to-bottom flow."
            ),
            (
                f"LOOK: {style} "
                "Consistent lighting, clean edges, readable silhouettes; avoid muddy shading."
            ),
            (
                "Typography rule (critical): Do not render any words, letters, numbers, captions, "
                "legends, speech bubbles, chemical formulas with characters, or UI chrome — models produce nonsense glyphs. "
                "Explain using plain arrows, colored blobs, light rays, and leaf anatomy only; think children's science "
                "picture book plate with the caption strip cropped off."
            ),
        ]
        ef = (self.educational_framing or "").strip()
        if ef:
            lines.append(
                f"VISUAL TEACHING AIDS (no text in image): {ef}"
            )
        lines.extend(
            [
                "CLARITY: sharp focus, high contrast for shapes, balanced palette, uncluttered background.",
                "SAFETY: classroom-appropriate, factual tone, no graphic violence, no sexual content, no hateful symbols.",
            ]
        )
        return "\n".join(lines)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> StructuredImagePrompt:
        """Build from a dict / JSON object (snake_case keys). Unknown keys ignored."""

        def pick(*keys: str) -> str:
            for k in keys:
                v = data.get(k)
                if v is not None and str(v).strip():
                    return str(v).strip()
            return ""

        topic = pick("topic", "subject")
        scene = pick("scene_description", "scene", "visual_description")
        style = pick("visual_style", "style", "art_style")
        framing = pick("educational_framing", "framing", "pedagogy", "teaching_notes")

        neg = data.get("negative_prompt")
        neg_s = str(neg).strip() if neg is not None else None
        if neg_s == "":
            neg_s = None

        ar = data.get("aspect_ratio")
        ar_s = str(ar).strip() if ar is not None else None
        if ar_s == "":
            ar_s = None

        if not topic:
            raise ValueError("structured prompt requires 'topic' (or 'subject')")
        if not scene:
            raise ValueError("structured prompt requires 'scene_description' (or 'scene')")
        if not style:
            raise ValueError("structured prompt requires 'visual_style' (or 'style')")

        return cls(
            topic=topic,
            scene_description=scene,
            visual_style=style,
            educational_framing=framing,
            negative_prompt=neg_s,
            aspect_ratio=ar_s,
        )
