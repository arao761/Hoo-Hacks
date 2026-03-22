# python
# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/config.py
import os
from functools import lru_cache


class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    job_ttl_seconds: int = 24 * 60 * 60
    redis_queue_key: str = "jobs:queue"
    redis_output_prefix: str = "output:"

    # TODO: add GEMINI / storage envs later, e.g.:
    # gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()