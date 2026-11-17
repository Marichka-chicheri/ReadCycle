"""Photos (avatars, book covers) live in a private S3 bucket.

Browsers upload straight to S3 with a presigned POST (size and type are enforced by S3 itself)
and show photos through short-lived presigned GET links. Nothing is ever public.
boto3 is created lazily so unit tests can replace `photo_url` / `upload_form` without AWS.
"""

import os
from functools import cache

URL_TTL_SECONDS = 6 * 3600  # how long a photo link in an API response stays valid
UPLOAD_TTL_SECONDS = 300
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@cache
def _s3():
    import boto3
    from botocore.config import Config

    # Regional, virtual-hosted URLs: the signature must match the bucket's own region.
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_REGION"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )


def _bucket() -> str:
    return os.environ["PHOTOS_BUCKET"]


def upload_form(key: str, content_type: str) -> dict:
    """{"url": ..., "fields": {...}} for a browser multipart POST of one file to `key`."""
    return _s3().generate_presigned_post(
        Bucket=_bucket(),
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, MAX_UPLOAD_BYTES],
        ],
        ExpiresIn=UPLOAD_TTL_SECONDS,
    )


def photo_url(key: str) -> str:
    """A temporary link to a stored photo, or "" when there is none."""
    if not key:
        return ""
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": _bucket(), "Key": key}, ExpiresIn=URL_TTL_SECONDS
    )


def delete_photo(key: str) -> None:
    if key:
        _s3().delete_object(Bucket=_bucket(), Key=key)
