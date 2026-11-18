"""Telegram alerts when a new book answers someone's wishlist.

Called right after a book is put on a shelf (POST /my/books). Best effort: it never fails the
request, skips students the owner blocked / who blocked the owner / who are banned, and sends
in parallel with a cap so a popular genre cannot slow the request down for long.
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor

from common import telegram
from common.db import main_table
from common.moderation import hidden_users
from domain.alerts import alert_text, wishers
from domain.book import Book
from repositories.catalog import CatalogRepository
from repositories.profiles import ProfileRepository
from repositories.telegram import TelegramRepository

log = logging.getLogger(__name__)

MAX_ALERTS = 40
PARALLEL = 8


def site_url() -> str:
    return os.environ.get("SITE_URL", "").rstrip("/")


def notify_wishers(book: Book) -> int:
    """Send alerts about `book`; returns how many were sent."""
    if not telegram.enabled() or book.is_given:
        return 0
    try:
        table = main_table()
        hidden = hidden_users(book.owner_id)
        targets = {
            uid: reason
            for uid, reason in wishers(book, CatalogRepository(table).all_wishes()).items()
            if uid not in hidden
        }
        if not targets:
            return 0
        links = TelegramRepository(table)
        chats = {uid: links.chat_id(uid) for uid in targets}
        chats = {uid: chat for uid, chat in chats.items() if chat}
        owner = ProfileRepository(table).get(book.owner_id)
        name = owner.display_name if owner else "Студент УКУ"
        url = site_url()
        button = ("Відкрити на ReadCycle", f"{url}/u/{book.owner_id}") if url else None

        jobs = [(chat, alert_text(book, targets[uid], name)) for uid, chat in chats.items()]
        with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
            sent = list(
                pool.map(lambda j: telegram.send_message(j[0], j[1], button), jobs[:MAX_ALERTS])
            )
        return sum(sent)
    except Exception:  # noqa: BLE001 - the book is saved; alerts are a bonus
        log.exception("telegram alerts for book %s failed", book.book_id)
        return 0
