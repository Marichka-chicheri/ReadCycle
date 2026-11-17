"""GET /books/lookup?q=<title, author or ISBN> — catalogue matches to auto-fill the book form."""

from common import book_lookup
from common.http import api_handler, current_user

MAX_QUERY = 150


@api_handler
def handler(event, context):
    current_user(event)
    q = str((event.get("queryStringParameters") or {}).get("q") or "")[:MAX_QUERY]
    return {"books": book_lookup.lookup_books(q)}
