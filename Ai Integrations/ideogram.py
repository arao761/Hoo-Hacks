"""Ideogram 3.0 image generation (REST).

Environment:
  IDEOGRAM_API_KEY

Docs: https://developer.ideogram.ai/api-reference/api-reference/generate-v3
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx

IDEOGRAM_GENERATE_V3_URL = "https://api.ideogram.ai/v1/ideogram-v3/generate"


@dataclass(frozen=True)
class IdeogramImageResult:
    image_bytes: bytes
    mime_type: str
    resolved_prompt: Optional[str] = None


def _api_key() -> str:
    key = os.environ.get("IDEOGRAM_API_KEY", "").strip()
    if not key:
        raise RuntimeError("IDEOGRAM_API_KEY is not set")
    return key


def generate_image_ideogram(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    aspect_ratio: str = "16x9",
    rendering_speed: str = "DEFAULT",
    negative_prompt: Optional[str] = None,
    num_images: int = 1,
    timeout_seconds: float = 120.0,
) -> IdeogramImageResult:
    """
    Synchronous Ideogram v3 generate; downloads the first image URL to bytes.

    aspect_ratio uses Ideogram's enum form, e.g. "1x1", "16x9", "4x3".
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be non-empty")

    key = api_key or _api_key()
    headers = {"Api-Key": key}

    files: list[tuple[str, tuple[None, str]]] = [
        ("prompt", (None, prompt.strip())),
        ("aspect_ratio", (None, aspect_ratio)),
        ("rendering_speed", (None, rendering_speed)),
        ("num_images", (None, str(num_images))),
    ]
    if negative_prompt:
        files.append(("negative_prompt", (None, negative_prompt)))

    with httpx.Client(timeout=timeout_seconds) as client:
        resp = client.post(
            IDEOGRAM_GENERATE_V3_URL,
            headers=headers,
            files=files,
        )

    if resp.status_code == 422:
        raise RuntimeError(f"Ideogram safety rejection: {resp.text}")
    resp.raise_for_status()

    payload = resp.json()
    items = payload.get("data") or []
    if not items:
        raise RuntimeError(f"Ideogram returned no data: {payload}")

    first: dict[str, Any] = items[0]
    url = first.get("url")
    if not url:
        if first.get("is_image_safe") is False:
            raise RuntimeError("Ideogram marked image unsafe; no URL returned")
        raise RuntimeError(f"Ideogram response missing url: {first}")

    resolved_prompt = first.get("prompt")

    with httpx.Client(timeout=timeout_seconds) as dl:
        img_resp = dl.get(url)
        img_resp.raise_for_status()

    content_type = img_resp.headers.get("content-type", "image/png")
    if "jpeg" in content_type or "jpg" in content_type:
        mime = "image/jpeg"
    elif "webp" in content_type:
        mime = "image/webp"
    else:
        mime = "image/png"

    return IdeogramImageResult(
        image_bytes=img_resp.content,
        mime_type=mime,
        resolved_prompt=resolved_prompt if isinstance(resolved_prompt, str) else None,
    )
