"""Single entrypoint for LearnLens image generation (Vertex Imagen 3 or Ideogram)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional, Union

from ideogram import IdeogramImageResult, generate_image_ideogram
from vertex_imagen import VertexImageResult, generate_image_vertex

ImageProvider = Literal["vertex", "ideogram"]

# Appended to every request — T2I models still hallucinate glyphs; this nudges harder.
_GLOBAL_NEGATIVE_TEXT = (
    "text, typography, letters, words, numbers, captions, subtitles, labels, callout boxes, "
    "annotations, speech bubbles, legends with writing, infographic text, lorem ipsum, "
    "gibberish writing, fake chemistry formulas, watermarks, logos, UI chrome"
)


def _merge_negative(user: Optional[str]) -> str:
    if user and user.strip():
        return f"{user.strip()}, {_GLOBAL_NEGATIVE_TEXT}"
    return _GLOBAL_NEGATIVE_TEXT


@dataclass(frozen=True)
class ImageGenerationOutput:
    image_bytes: bytes
    mime_type: str
    provider: ImageProvider
    model_or_vendor: str
    enhanced_or_resolved_prompt: Optional[str] = None


def _resolve_provider(explicit: Optional[str]) -> ImageProvider:
    raw = (explicit or os.environ.get("LEARNLENS_IMAGE_PROVIDER", "vertex")).strip().lower()
    if raw in ("vertex", "imagen", "vertex_imagen", "google"):
        return "vertex"
    if raw in ("ideogram", "ideo"):
        return "ideogram"
    raise ValueError(
        f"Unknown LEARNLENS_IMAGE_PROVIDER={raw!r}; use 'vertex' or 'ideogram'"
    )


def generate_learnlens_image(
    prompt: str,
    *,
    provider: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    negative_prompt: Optional[str] = None,
) -> ImageGenerationOutput:
    """
    Generate one educational-style image as bytes (hand off to R2/S3 upload elsewhere).

    - Vertex: aspect_ratio like "16:9" (colon). Uses VERTEX_IMAGEN_MODEL (default Imagen 3).
    - Ideogram: aspect_ratio like "16x9" (x). Defaults to 16x9 if omitted.
    """
    which = _resolve_provider(provider)

    merged_neg = _merge_negative(negative_prompt)

    if which == "vertex":
        v_aspect = aspect_ratio
        if v_aspect and "x" in v_aspect and ":" not in v_aspect:
            v_aspect = v_aspect.replace("x", ":", 1)
        result: Union[VertexImageResult, IdeogramImageResult] = generate_image_vertex(
            prompt,
            aspect_ratio=v_aspect,
            negative_prompt=merged_neg,
            number_of_images=1,
            enhance_prompt=False,
        )
        assert isinstance(result, VertexImageResult)
        return ImageGenerationOutput(
            image_bytes=result.image_bytes,
            mime_type=result.mime_type,
            provider="vertex",
            model_or_vendor=result.model,
            enhanced_or_resolved_prompt=result.enhanced_prompt,
        )

    i_aspect = aspect_ratio or "16x9"
    if i_aspect and ":" in i_aspect:
        i_aspect = i_aspect.replace(":", "x", 1)

    idg = generate_image_ideogram(
        prompt,
        aspect_ratio=i_aspect,
        negative_prompt=merged_neg,
        num_images=1,
    )
    return ImageGenerationOutput(
        image_bytes=idg.image_bytes,
        mime_type=idg.mime_type,
        provider="ideogram",
        model_or_vendor="ideogram-v3",
        enhanced_or_resolved_prompt=idg.resolved_prompt,
    )
