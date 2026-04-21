import uuid
import boto3
from botocore.config import Config
from django.conf import settings


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def generate_download_url(s3_key: str, filename: str, expires_in: int = 300) -> str:
    """Generates a presigned GET URL for downloading an S3 object."""
    return get_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        },
        ExpiresIn=expires_in,
    )


def generate_upload_url(owner_id: str, filename: str) -> tuple[str, str]:
    """
    Generates a presigned PUT URL and the corresponding s3_key.
    Returns (presigned_url, s3_key).
    """
    s3_key = f"raw/{owner_id}/{uuid.uuid4()}/{filename}"
    url = get_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key, "ContentType": "application/octet-stream"},
        ExpiresIn=300,
    )
    return url, s3_key
