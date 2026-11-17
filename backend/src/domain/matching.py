"""Matching: who could exchange books with whom.

A *book* (someone's shelf) satisfies a *wish* (someone else's wishlist) when:
- wish kind "book":  the titles match (case, quotes and punctuation ignored; one title fully
  contained in the other also counts) and, if the wish names an author, the surnames match;
- wish kind "genre": the genres are equal;
- in both cases, if the wish names a language, the book must be in that language.

For the signed-in user every other user falls into one of three groups:
- MUTUAL   — each has something from the other's wishlist (a real exchange);
- FOR_ME   — they have something I want (a free book is the best case);
- FOR_THEM — they want something from my shelf.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from domain.book import OFFER_GIVE, Book
from domain.catalog import fold
from domain.wish import KIND_BOOK, Wish

MUTUAL = "mutual"
FOR_ME = "for_me"
FOR_THEM = "for_them"
KIND_ORDER = {MUTUAL: 0, FOR_ME: 1, FOR_THEM: 2}

SCORE_TITLE = 3  # a book from the wishlist by name
SCORE_GENRE = 1  # "anything in this genre"
SCORE_FREE = 1  # bonus: given away for free
MIN_CONTAINED_TITLE = 5  # "Дюна" must not match every title containing "дюна"-like short words

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def normalize_title(text: str) -> str:
    return " ".join(_PUNCT.sub(" ", fold(text)).split())


def surname(author: str) -> str:
    words = normalize_title(author).split()
    return words[-1] if words else ""


def titles_match(wanted: str, offered: str) -> bool:
    a, b = normalize_title(wanted), normalize_title(offered)
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = sorted((a, b), key=len)
    return len(shorter) >= MIN_CONTAINED_TITLE and f" {shorter} " in f" {longer} "


def authors_match(wanted: str, offered: str) -> bool:
    want = surname(wanted)
    return not want or want in normalize_title(offered).split()


@dataclass(frozen=True)
class Reason:
    """Why a book satisfies a wish."""

    wish: Wish
    by: str  # "title" | "genre"

    @property
    def score(self) -> int:
        return SCORE_TITLE if self.by == "title" else SCORE_GENRE


def satisfies(book: Book, wish: Wish) -> Reason | None:
    if book.owner_id == wish.owner_id:
        return None
    if wish.language and book.language != wish.language:
        return None
    if wish.kind == KIND_BOOK:
        if titles_match(wish.title, book.title) and authors_match(wish.author, book.author):
            return Reason(wish, "title")
        return None
    if wish.genre and book.genre == wish.genre:
        return Reason(wish, "genre")
    return None


@dataclass(frozen=True)
class BookMatch:
    book: Book
    reason: Reason

    @property
    def score(self) -> int:
        return self.reason.score + (SCORE_FREE if self.book.offer == OFFER_GIVE else 0)

    def to_json(self) -> dict:
        return {
            "book": self.book.to_json(),
            "by": self.reason.by,
            "wish": self.reason.wish.to_json(),
        }


def _best_per_book(matches: list[BookMatch]) -> list[BookMatch]:
    """One entry per book (the strongest reason), best first."""
    best: dict[str, BookMatch] = {}
    for m in matches:
        if m.book.book_id not in best or m.score > best[m.book.book_id].score:
            best[m.book.book_id] = m
    return sorted(best.values(), key=lambda m: (-m.score, m.book.title))


@dataclass
class Match:
    user_id: str
    they_have: list[BookMatch] = field(default_factory=list)  # their books I want
    they_want: list[BookMatch] = field(default_factory=list)  # my books they want

    @property
    def kind(self) -> str:
        if self.they_have and self.they_want:
            return MUTUAL
        return FOR_ME if self.they_have else FOR_THEM

    @property
    def score(self) -> int:
        return sum(m.score for m in self.they_have) + sum(m.score for m in self.they_want)

    def sort_key(self) -> tuple:
        return (KIND_ORDER[self.kind], -self.score)


def find_matches(viewer_id: str, books: list[Book], wishes: list[Wish]) -> list[Match]:
    """All matches for `viewer_id`, best first. `books`/`wishes` are everyone's (incl. viewer's)."""
    books = [b for b in books if not b.is_given]  # given away: nothing to exchange any more
    my_books = [b for b in books if b.owner_id == viewer_id]
    my_wishes = [w for w in wishes if w.owner_id == viewer_id]
    their_books = [b for b in books if b.owner_id != viewer_id]
    their_wishes = [w for w in wishes if w.owner_id != viewer_id]

    have: dict[str, list[BookMatch]] = defaultdict(list)
    want: dict[str, list[BookMatch]] = defaultdict(list)
    for book in their_books:
        for wish in my_wishes:
            if reason := satisfies(book, wish):
                have[book.owner_id].append(BookMatch(book, reason))
    for wish in their_wishes:
        for book in my_books:
            if reason := satisfies(book, wish):
                want[wish.owner_id].append(BookMatch(book, reason))

    matches = [
        Match(uid, _best_per_book(have.get(uid, [])), _best_per_book(want.get(uid, [])))
        for uid in set(have) | set(want)
    ]
    return sorted(matches, key=Match.sort_key)
