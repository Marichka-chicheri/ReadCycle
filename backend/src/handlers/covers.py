"""GET /covers/search?title=...&author=...  (or ?q=free text) — cover candidates for a book.

The browser cannot use Google Books directly (the shared anonymous quota is exhausted), so the
search runs here with the project's own API key. See common/cover_sources.py.
"""

from common import cover_sources
from common.http import api_handler, current_user

MAX_FIELD = 150


@api_handler
def handler(event, context):
    current_user(event)
    params = event.get("queryStringParameters") or {}
    title = str(params.get("title") or "")[:MAX_FIELD]
    author = str(params.get("author") or "")[:MAX_FIELD]
    query = str(params.get("q") or "")[:MAX_FIELD]
    return {
        "covers": cover_sources.search_covers(title, author, query),
        "google": bool(cover_sources.google_key()),
    }
