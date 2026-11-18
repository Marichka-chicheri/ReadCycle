"""Which wishlists a newly shelved book answers, and the Telegram message about it.

Uses the same rules as matching (domain.matching.satisfies). Each student gets at most one
alert per book, about their strongest reason: a wish for this very title beats "anything in
this genre".
"""

from __future__ import annotations

from html import escape

from common.genres import GENRES
from domain.book import OFFER_GIVE, Book
from domain.matching import Reason, satisfies
from domain.wish import Wish


def wishers(book: Book, wishes: list[Wish]) -> dict[str, Reason]:
    """owner id -> why this book is for them (the book owner never alerts themselves)."""
    best: dict[str, Reason] = {}
    for wish in wishes:
        reason = satisfies(book, wish)
        if reason and (wish.owner_id not in best or reason.score > best[wish.owner_id].score):
            best[wish.owner_id] = reason
    best.pop(book.owner_id, None)
    return best


def alert_text(book: Book, reason: Reason, owner_name: str) -> str:
    title = f"«{escape(book.title)}» — {escape(book.author)}"
    if reason.by == "title":
        head = "📚 На ReadCycle з'явилася книга з твого вішліста!"
    else:
        head = (
            f"📚 Нова книга в жанрі, який ти шукаєш ({escape(GENRES.get(book.genre, book.genre))}):"
        )
    offer = "віддає безкоштовно" if book.offer == OFFER_GIVE else "готова обміняти"
    return f"{head}\n\n<b>{title}</b>\n{escape(owner_name)} {offer}."
