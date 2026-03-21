import os
from dotenv import load_dotenv

load_dotenv()

# Redis (Upstash or local)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Cloudflare R2
R2_ACCOUNT_ID      = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID   = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY      = os.getenv("R2_SECRET_KEY")
R2_BUCKET_NAME     = os.getenv("R2_BUCKET_NAME", "learnlens-media")
R2_PUBLIC_URL      = os.getenv("R2_PUBLIC_URL")  # e.g. https://pub-xxx.r2.dev

# Job queue
QUEUE_KEY      = "queue:jobs"
JOB_TTL        = 60 * 60 * 24  # 24 hours in seconds
CACHE_TTL      = 60 * 60 * 24  # 24 hours in seconds
