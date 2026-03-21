# python
# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/storage.py
import uuid
from typing import Literal


def upload_media_and_get_cdn_url(
    content_bytes: bytes,
    media_type: Literal["image", "song", "video"],
) -> str:
    """
    Person 2 just defines the interface.
    Person 4 / infra will wire Cloudflare R2 / S3 + CDN.
    """
    fake_id = uuid.uuid4().hex
    ext = {"image": "png", "song": "mp3", "video": "mp4"}[media_type]
    # Placeholder; infra team replaces with real CDN base URL.
    return f"https://cdn.example.com/{media_type}/{fake_id}.{ext}"