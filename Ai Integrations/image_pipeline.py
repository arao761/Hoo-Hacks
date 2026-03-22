"""Structured prompt → image bytes → optional storage handoff."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

from image_generation import ImageGenerationOutput, generate_learnlens_image
from storage_handoff import ImageStorageSink, StoredImageRef
from educational_topic_presets import get_preset
from structured_image_prompt import StructuredImagePrompt


StructuredInput = Union[StructuredImagePrompt, Mapping[str, Any]]


@dataclass(frozen=True)
class StructuredImagePipelineResult:
    """Bytes for immediate use (preview, workers) plus CDN ref when storage ran."""

    generation: ImageGenerationOutput
    stored: Optional[StoredImageRef]


def coerce_structured(data: StructuredInput) -> StructuredImagePrompt:
    if isinstance(data, StructuredImagePrompt):
        return data
    return StructuredImagePrompt.from_mapping(data)


def generate_image_from_topic_preset(
    slug: str,
    *,
    provider: Optional[str] = None,
) -> ImageGenerationOutput:
    """Run the pipeline using a built-in educational preset (see `educational_topic_presets.PRESET_SLUGS`)."""
    return generate_image_from_structured_prompt(get_preset(slug), provider=provider)


def generate_image_from_structured_prompt(
    structured: StructuredInput,
    *,
    provider: Optional[str] = None,
) -> ImageGenerationOutput:
    """
    Turn Gemini-style structured fields into one T2I prompt, then return image bytes + metadata.
    """
    s = coerce_structured(structured)
    return generate_learnlens_image(
        s.to_model_prompt(),
        provider=provider,
        aspect_ratio=s.aspect_ratio,
        negative_prompt=s.negative_prompt,
    )


def generate_image_from_structured_prompt_and_store(
    structured: StructuredInput,
    storage: ImageStorageSink,
    *,
    provider: Optional[str] = None,
    basename_hint: str = "learnlens",
) -> StructuredImagePipelineResult:
    """
    Generate from structured prompt, then hand bytes to the storage layer.

    `storage` should be your R2/S3 uploader (same responsibility as upload_media()).
    """
    gen = generate_image_from_structured_prompt(structured, provider=provider)
    ref = storage.store_image(
        data=gen.image_bytes,
        content_type=gen.mime_type,
        basename_hint=basename_hint,
    )
    return StructuredImagePipelineResult(generation=gen, stored=ref)
