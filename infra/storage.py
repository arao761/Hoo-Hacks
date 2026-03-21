import boto3
import uuid
from infra.config import S3_ACCESS_KEY_ID, S3_SECRET_KEY, S3_REGION, S3_BUCKET_NAME

_s3 = None


def _get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_KEY,
        )
    return _s3


CONTENT_TYPE_EXT = {
    "image/png":  "png",
    "image/jpeg": "jpg",
    "audio/mpeg": "mp3",
    "audio/wav":  "wav",
    "video/mp4":  "mp4",
}


def upload_media(data: bytes, content_type: str, job_id: str = None) -> str:
    """
    Called by Person 3's AI modules after generation.
    Uploads raw bytes to S3 and returns a public HTTPS URL.

    Args:
        data:         raw file bytes (image, audio, or video)
        content_type: MIME type e.g. "audio/mpeg", "image/png", "video/mp4"
        job_id:       optional, used as part of the filename for traceability

    Returns:
        Public S3 URL string
    """
    ext = CONTENT_TYPE_EXT.get(content_type, "bin")
    prefix = job_id or str(uuid.uuid4())
    key = f"outputs/{prefix}.{ext}"

    s3 = _get_s3()
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
    )

    return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{key}"
