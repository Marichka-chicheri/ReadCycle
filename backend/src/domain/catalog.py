"""Catalog search: everyone else's books, filtered by text, genre, language and offer."""

from __future__ import annotations

from dataclasses import dataclass

from common.genres import is_genre
from common.http import ValidationError
from common.languages import is_language
from domain.book import OFFERS, Book

MAX_QUERY = 100


def fold(text: str) -> str:
    """Case- and apostrophe-insensitive form for substring search."""
    return text.casefold().replace("’", "'").replace("ʼ", "'")


@dataclass(frozen=True)
class CatalogFilter:
    q: str = ""
    genre: str = ""
    language: str = ""
    offer: str = ""

    @classmethod
    def from_query(cls, params: dict | None) -> CatalogFilter:
        params = params or {}
        f = cls(
            q=" ".join(str(params.get("q") or "").split())[:MAX_QUERY],
            genre=str(params.get("genre") or ""),
            language=str(params.get("language") or ""),
            offer=str(params.get("offer") or ""),
        )
        errors = {}
        if f.genre and not is_genre(f.genre):
            errors["genre"] = "Невідомий жанр"
        if f.language and not is_language(f.language):
            errors["language"] = "Невідома мова"
        if f.offer and f.offer not in OFFERS:
            errors["offer"] = "Невідомий тип"
        if errors:
            raise ValidationError(errors)
        return f

    def matches(self, book: Book) -> bool:
        if self.genre and book.genre != self.genre:
            return False
        if self.language and book.language != self.language:
            return False
        if self.offer and book.offer != self.offer:
            return False
        if self.q:
            haystack = fold(f"{book.title} {book.author}")
            return all(word in haystack for word in fold(self.q).split())
        return True
