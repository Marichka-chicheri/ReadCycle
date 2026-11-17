"""A wishlist entry. Two kinds:

- "book":  a specific book — title required, author/genre/language optional;
- "genre": "anything in this genre" — genre required, language optional.

Stored as pk=USER#<owner>, sk=WISH#<id>, plus gsi1pk="WISH" so matching (stage 6) can read
every wish through the same catalog index as books.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any

from common.genres import is_genre
from common.http import ValidationError
from common.languages import is_language
from domain.book import AUTHOR_MAX, TITLE_MAX, clean_text
from domain.media import is_allowed_cover_url
from domain.profile import now_iso

KIND_BOOK = "book"
KIND_GENRE = "genre"
KINDS = (KIND_BOOK, KIND_GENRE)
NOTE_MAX = 300


@dataclass
class Wish:
    wish_id: str
    owner_id: str
    kind: str
    title: str = ""
    author: str = ""
    genre: str = ""
    language: str = ""
    note: str = ""
    cover_url: str = ""  # optional cover picked from the catalogue (book wishes only)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_input(cls, owner_id: str, data: dict[str, Any], existing: Wish | None = None) -> Wish:
        errors: dict[str, str] = {}

        kind = str(data.get("kind") or "")
        if kind not in KINDS:
            raise ValidationError({"kind": "Оберіть: конкретна книга чи жанр"})

        title = author = ""
        if kind == KIND_BOOK:
            title = clean_text(data.get("title"))
            if not 1 <= len(title) <= TITLE_MAX:
                errors["title"] = f"Вкажіть назву (до {TITLE_MAX} символів)"
            author = clean_text(data.get("author"))
            if len(author) > AUTHOR_MAX:
                errors["author"] = f"До {AUTHOR_MAX} символів"

        genre = str(data.get("genre") or "")
        if kind == KIND_GENRE and not genre:
            errors["genre"] = "Оберіть жанр"
        elif genre and not is_genre(genre):
            errors["genre"] = "Невідомий жанр"

        language = str(data.get("language") or "")
        if language and not is_language(language):
            errors["language"] = "Невідома мова"

        cover_url = str(data.get("cover_url") or "").strip() if kind == KIND_BOOK else ""
        if cover_url and not is_allowed_cover_url(cover_url):
            errors["cover_url"] = "Цю обкладинку не вдалося додати"

        note = str(data.get("note") or "").strip()
        if len(note) > NOTE_MAX:
            errors["note"] = f"Не більше {NOTE_MAX} символів"

        if errors:
            raise ValidationError(errors)

        ts = now_iso()
        return cls(
            wish_id=existing.wish_id if existing else uuid.uuid4().hex[:12],
            owner_id=owner_id,
            kind=kind,
            title=title,
            author=author,
            genre=genre,
            language=language,
            note=note,
            cover_url=cover_url,
            created_at=existing.created_at if existing else ts,
            updated_at=ts,
        )

    @property
    def id(self) -> str:
        return self.wish_id

    def to_item(self) -> dict[str, Any]:
        return {
            "pk": f"USER#{self.owner_id}",
            "sk": f"WISH#{self.wish_id}",
            "type": "WISH",
            "gsi1pk": "WISH",
            "gsi1sk": f"{self.created_at}#{self.wish_id}",
            **asdict(self),
        }

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Wish:
        return cls(**{f: item.get(f, "") for f in cls.__dataclass_fields__})

    def to_json(self) -> dict[str, Any]:
        return asdict(self)
