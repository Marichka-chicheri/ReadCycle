"""Rules for pictures attached to profiles and books.

- Uploaded photos are S3 keys under the owner's own prefix:
    avatars/<user_id>/<random>   and   covers/<user_id>/<random>
  so nobody can attach (or later delete) another person's file.
- A book cover can instead be a link to a known book-cover service (picked from search results).
"""

from __future__ import annotations

import re
import uuid
from urllib.parse import urlparse

KIND_AVATAR = "avatar"
KIND_COVER = "cover"
PREFIXES = {KIND_AVATAR: "avatars", KIND_COVER: "covers"}
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

# Cover search (frontend) uses Google Books and Open Library; only their image hosts are accepted.
COVER_HOSTS = ("books.google.com", "books.googleusercontent.com", "covers.openlibrary.org")
COVER_URL_MAX = 500

_KEY_RE = re.compile(r"^[a-z]+/[A-Za-z0-9-]+/[a-f0-9]{32}\.(jpg|png|webp)$")


def new_photo_key(kind: str, user_id: str, content_type: str) -> str:
    return f"{PREFIXES[kind]}/{user_id}/{uuid.uuid4().hex}.{IMAGE_TYPES[content_type]}"


def is_own_photo_key(key: str, kind: str, user_id: str) -> bool:
    return bool(_KEY_RE.match(key)) and key.startswith(f"{PREFIXES[kind]}/{user_id}/")


def is_allowed_cover_url(url: str) -> bool:
    if not url or len(url) > COVER_URL_MAX:
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        host == h or host.endswith("." + h) for h in COVER_HOSTS
    )
