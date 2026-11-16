"""Book photos live in a private S3 bucket; clients upload/download via presigned URLs."""

import os

import boto3

_s3 = boto3.client("s3")


def presigned_upload_url(key: str, content_type: str, expires: int = 300) -> str:
    return _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": os.environ["PHOTOS_BUCKET"], "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presigned_download_url(key: str, expires: int = 3600) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": os.environ["PHOTOS_BUCKET"], "Key": key},
        ExpiresIn=expires,
    )
