"""POST /uploads — permission to upload one photo straight to S3.

Body: {"kind": "avatar" | "cover", "content_type": "image/jpeg" | "image/png" | "image/webp"}
Returns {"key", "url", "fields"}: the browser POSTs the file to `url` with `fields`, then saves
`key` as the profile's `avatar_key` or the book's `cover_key`.
"""

from common import storage
from common.http import ValidationError, api_handler, current_user, json_body
from domain.media import IMAGE_TYPES, PREFIXES, new_photo_key


@api_handler
def handler(event, context):
    user_id, _ = current_user(event)
    data = json_body(event)
    kind = str(data.get("kind") or "")
    content_type = str(data.get("content_type") or "")

    errors = {}
    if kind not in PREFIXES:
        errors["kind"] = "Невідомий тип фото"
    if content_type not in IMAGE_TYPES:
        errors["content_type"] = "Підійде JPG, PNG або WEBP"
    if errors:
        raise ValidationError(errors)

    key = new_photo_key(kind, user_id, content_type)
    form = storage.upload_form(key, content_type)
    return {
        "key": key,
        "url": form["url"],
        "fields": form["fields"],
        "max_bytes": storage.MAX_UPLOAD_BYTES,
    }
