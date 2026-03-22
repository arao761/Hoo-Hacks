"""Contracts for handing generated media bytes to R2/S3 (implemented by infra / FastAPI)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class StoredImageRef:
    """Return value after uploading an image to object storage + CDN."""

    url: str
    object_key: str
    content_type: str


@dataclass(frozen=True)
class StoredAudioRef:
    """Return value after uploading audio (e.g. Lyria WAV) to object storage + CDN."""

    url: str
    object_key: str
    content_type: str


@dataclass(frozen=True)
class StoredVideoRef:
    """Return value after uploading video (e.g. Runway Gen-4 MP4) to object storage + CDN."""

    url: str
    object_key: str
    content_type: str


@runtime_checkable
class ImageStorageSink(Protocol):
    """Implement on your storage helper (e.g. upload_media) and pass into the image pipeline."""

    def store_image(
        self,
        *,
        data: bytes,
        content_type: str,
        basename_hint: str = "learnlens",
    ) -> StoredImageRef:
        """Upload bytes; return public or signed CDN URL and object key."""
        ...


@runtime_checkable
class AudioStorageSink(Protocol):
    """Same as image sink but for WAV/MP3 from Lyria — can wrap the same upload_media()."""

    def store_audio(
        self,
        *,
        data: bytes,
        content_type: str,
        basename_hint: str = "learnlens",
    ) -> StoredAudioRef:
        """Upload audio bytes; return CDN URL and object key."""
        ...


@runtime_checkable
class VideoStorageSink(Protocol):
    """Implement for Runway (or other) video bytes — can reuse the same upload helper as images."""

    def store_video(
        self,
        *,
        data: bytes,
        content_type: str,
        basename_hint: str = "learnlens",
    ) -> StoredVideoRef:
        """Upload video bytes; return CDN URL and object key."""
        ...
