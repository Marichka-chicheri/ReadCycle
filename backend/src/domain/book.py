"""A book that its owner is ready to give away or exchange.

Stored as pk=USER#<owner>, sk=BOOK#<id>, so one query returns a user's whole shelf.
Every book also carries gsi1pk="BOOK" / gsi1sk=<created_at>#<id>: the catalog index
(added on stage 5) uses these to list everyone's books, newest first.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from common import storage
from common.genres import is_genre
from common.http import ValidationError
from common.languages import is_language
from domain.book_metadata import normalize_isbn
from domain.language_policy import is_russian_isbn, russian_fields
from domain.media import KIND_COVER, is_allowed_cover_url, is_own_photo_key
from domain.profile import now_iso

TITLE_MAX = 150
AUTHOR_MAX = 100
DESCRIPTION_MAX = 1000
YEAR_MIN = 1450  # Gutenberg; anything earlier is a typo


def _this_year() -> int:
    return datetime.now(UTC).year


OFFER_GIVE = "give"  # віддам безкоштовно
OFFER_EXCHANGE = "exchange"  # лише обмін
OFFERS = (OFFER_GIVE, OFFER_EXCHANGE)

STATUS_AVAILABLE = "available"  # на полиці, можна забрати
STATUS_GIVEN = "given"  # віддана: зникає з каталогу й підбору обміну, на полиці напівпрозора
STATUSES = (STATUS_AVAILABLE, STATUS_GIVEN)


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


@dataclass
class Book:
    book_id: str
    owner_id: str
    title: str
    author: str
    language: str
    genre: str
    offer: str
    description: str = ""
    year: str = ""  # year of this edition, "" if unknown
    isbn: str = ""  # ISBN-10/13 digits only, "" if unknown
    cover_key: str = ""  # uploaded photo (S3 key under covers/<owner>/)
    cover_url: str = ""  # or a picture picked from cover search (Google Books / Open Library)
    status: str = STATUS_AVAILABLE
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_input(cls, owner_id: str, data: dict[str, Any], existing: Book | None = None) -> Book:
        errors: dict[str, str] = {}

        title = clean_text(data.get("title"))
        if not 1 <= len(title) <= TITLE_MAX:
            errors["title"] = f"Вкажіть назву (до {TITLE_MAX} символів)"

        author = clean_text(data.get("author"))
        if not 1 <= len(author) <= AUTHOR_MAX:
            errors["author"] = f"Вкажіть автора (до {AUTHOR_MAX} символів)"

        language = str(data.get("language") or "")
        if not is_language(language):
            errors["language"] = "Оберіть мову"

        genre = str(data.get("genre") or "")
        if not is_genre(genre):
            errors["genre"] = "Оберіть жанр"

        offer = str(data.get("offer") or "")
        if offer not in OFFERS:
            errors["offer"] = "Оберіть: віддам чи обміняю"

        # an edit that does not mention the status keeps the current one
        status = str(data.get("status") or (existing.status if existing else STATUS_AVAILABLE))
        if status not in STATUSES:
            errors["status"] = "Невідомий статус"

        description = str(data.get("description") or "").strip()
        if len(description) > DESCRIPTION_MAX:
            errors["description"] = f"Не більше {DESCRIPTION_MAX} символів"

        year = str(data.get("year") or "").strip()
        if year and not (year.isdigit() and YEAR_MIN <= int(year) <= _this_year() + 1):
            errors["year"] = f"Рік від {YEAR_MIN} до {_this_year() + 1}"

        isbn_raw = str(data.get("isbn") or "").strip()
        isbn = normalize_isbn(isbn_raw)
        if isbn_raw and not isbn:
            errors["isbn"] = "ISBN має 10 або 13 цифр"
        elif isbn and is_russian_isbn(isbn):
            errors["isbn"] = "Це ISBN російського видання: такі книги на ReadCycle не додаються"

        for name, message in russian_fields(
            title=title, author=author, description=description
        ).items():
            errors.setdefault(name, message)

        cover_key = str(data.get("cover_key") or "")
        cover_url = str(data.get("cover_url") or "").strip()
        if cover_key and not is_own_photo_key(cover_key, KIND_COVER, owner_id):
            errors["cover"] = "Фото не знайдено, завантажте його ще раз"
        elif cover_url and not is_allowed_cover_url(cover_url):
            errors["cover"] = "Цю обкладинку не вдалося додати"
        if cover_key:
            cover_url = ""  # an uploaded photo wins over a found one

        if errors:
            raise ValidationError(errors)

        ts = now_iso()
        return cls(
            book_id=existing.book_id if existing else uuid.uuid4().hex[:12],
            owner_id=owner_id,
            title=title,
            author=author,
            language=language,
            genre=genre,
            offer=offer,
            description=description,
            year=year,
            isbn=isbn,
            cover_key=cover_key,
            cover_url=cover_url,
            status=status,
            created_at=existing.created_at if existing else ts,
            updated_at=ts,
        )

    @property
    def id(self) -> str:
        return self.book_id

    def to_item(self) -> dict[str, Any]:
        return {
            "pk": f"USER#{self.owner_id}",
            "sk": f"BOOK#{self.book_id}",
            "type": "BOOK",
            "gsi1pk": "BOOK",
            "gsi1sk": f"{self.created_at}#{self.book_id}",
            **asdict(self),
        }

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Book:
        book = cls(**{f: item.get(f, "") for f in cls.__dataclass_fields__})
        if book.status not in STATUSES:  # saved before statuses existed (or the old "reserved")
            book.status = STATUS_AVAILABLE
        return book

    @property
    def is_given(self) -> bool:
        return self.status == STATUS_GIVEN

    def photo_keys(self) -> set[str]:
        return {self.cover_key} if self.cover_key else set()

    def to_json(self) -> dict[str, Any]:
        # cover_src: what the browser shows — a temporary link to the uploaded photo, or the
        # found cover's URL, or "" (then the frontend draws a cloth-bound cover).
        return {**asdict(self), "cover_src": storage.photo_url(self.cover_key) or self.cover_url}
