import os
from dotenv import load_dotenv

load_dotenv()

# Redis (Upstash or local)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# AWS S3
S3_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_REGION        = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME   = os.getenv("S3_BUCKET_NAME", "learnlens-media")

# Job queue / cache
QUEUE_KEY  = "jobs:queue"  # must match backend/config.py redis_queue_key
JOB_TTL    = 60 * 60 * 24  # 24 hours in seconds
CACHE_TTL  = 60 * 60 * 24  # 24 hours in seconds
