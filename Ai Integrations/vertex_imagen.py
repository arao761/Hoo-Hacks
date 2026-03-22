"""Imagen on Vertex AI via the unified google-genai client.

Environment (Vertex):
  GOOGLE_CLOUD_PROJECT
  GOOGLE_CLOUD_LOCATION  (e.g. us-central1, or global per current Google samples)
  GOOGLE_GENAI_USE_VERTEXAI=True

Auth: Application Default Credentials (gcloud auth application-default login) or
workload identity in cloud.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai.types import GenerateImagesConfig


DEFAULT_MODEL = os.environ.get("VERTEX_IMAGEN_MODEL", "imagen-3.0-generate-002")


@dataclass(frozen=True)
class VertexImageResult:
    image_bytes: bytes
    mime_type: str
    model: str
    enhanced_prompt: Optional[str] = None


def generate_image_vertex(
    prompt: str,
    *,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    number_of_images: int = 1,
    output_mime_type: str = "image/png",
    enhance_prompt: bool = False,
) -> VertexImageResult:
    """
    Text-to-image using Imagen on Vertex. Returns raw image bytes for storage upload.

    aspect_ratio examples: "1:1", "16:9", "9:16", "4:3", "3:4"
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be non-empty")

    resolved_model = model or DEFAULT_MODEL
    config_kwargs: dict = {
        "number_of_images": number_of_images,
        "output_mime_type": output_mime_type,
        # Prompt rewriter often adds “poster / label” language → fake text in-image.
        "enhance_prompt": enhance_prompt,
    }
    if aspect_ratio:
        config_kwargs["aspect_ratio"] = aspect_ratio
    if negative_prompt:
        config_kwargs["negative_prompt"] = negative_prompt

    config = GenerateImagesConfig(**config_kwargs)
    client = genai.Client()

    response = client.models.generate_images(
        model=resolved_model,
        prompt=prompt.strip(),
        config=config,
    )

    if not response.generated_images:
        raise RuntimeError("Vertex Imagen returned no images (empty generated_images)")

    first = response.generated_images[0]
    if first.rai_filtered_reason:
        raise RuntimeError(f"Vertex Imagen filtered output: {first.rai_filtered_reason}")

    img = first.image
    if not img or not img.image_bytes:
        raise RuntimeError("Vertex Imagen returned no image bytes")

    enhanced = getattr(first, "enhanced_prompt", None)
    mime = img.mime_type or output_mime_type

    return VertexImageResult(
        image_bytes=img.image_bytes,
        mime_type=mime,
        model=resolved_model,
        enhanced_prompt=enhanced,
    )
