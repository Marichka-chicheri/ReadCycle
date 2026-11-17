import pytest

from common import book_lookup, cover_sources
from common.http import ValidationError
from domain.book import Book
from domain.language_policy import is_russian_book, is_russian_isbn, is_russian_text
from domain.wish import Wish


@pytest.mark.parametrize(
    "text",
    [
        "Мастер и Маргарита",
        "Война и мир",
        "Преступление и наказание",
        "Отцы и дети",
        "Тёмные аллеи",  # ё
        "Мы",  # ы
        "Подъезд",  # ъ
        "Это всё",
        "Что делать?",
    ],
)
def test_russian_text(text):
    assert is_russian_text(text)


@pytest.mark.parametrize(
    "text",
    [
        "Майстер і Маргарита",
        "Тіні забутих предків",
        "Енеїда",
        "Тигролови",  # no Ukrainian-only letter, but nothing Russian either
        "Сто років самотності",
        "Ґречність",
        "Дзеці і пчолы",  # Belarusian (ы, but also і)
        "Dune",
        "Ми",
        "",
    ],
)
def test_not_russian_text(text):
    assert not is_russian_text(text)


def test_isbn_and_language_codes():
    assert is_russian_isbn("9785170987654")
    assert is_russian_isbn("5170987654")
    assert not is_russian_isbn("9786177561438")
    assert not is_russian_isbn("9789662355574")
    assert is_russian_book("Идиот", languages=["rus"])
    assert is_russian_book("Ідіот", isbn="9785170987654")
    # Open Library lists every edition's language: a Ukrainian work translated into Russian stays
    assert not is_russian_book("Тіні забутих предків", languages=["ukr", "rus"])


BOOK = {"title": "Дюна", "author": "Френк Герберт", "language": "uk", "genre": "scifi"}


@pytest.mark.parametrize(
    "field, value",
    [
        ("title", "Мастер и Маргарита"),
        ("author", "Фёдор Достоевский"),
        ("description", "Хорошая книга, почти новая"),
        ("isbn", "978-5-17-098765-4"),
    ],
)
def test_russian_books_cannot_be_added(field, value):
    with pytest.raises(ValidationError) as e:
        Book.from_input("u", {**BOOK, "offer": "give", field: value})
    assert field in e.value.fields


def test_russian_wish_is_rejected():
    with pytest.raises(ValidationError) as e:
        Wish.from_input("u", {"kind": "book", "title": "Война и мир"})
    assert "title" in e.value.fields
    assert Wish.from_input("u", {"kind": "book", "title": "Війна і мир"}).title == "Війна і мир"


GOOGLE = {
    "items": [
        {
            "volumeInfo": {
                "title": "Дюна",
                "language": "uk",
                "imageLinks": {"thumbnail": "https://g/1"},
            }
        },
        {
            "volumeInfo": {
                "title": "Дюна",
                "language": "ru",
                "imageLinks": {"thumbnail": "https://g/2"},
            }
        },
        {  # not marked as Russian, but a Russian ISBN
            "volumeInfo": {
                "title": "Dune",
                "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9785171234567"}],
                "imageLinks": {"thumbnail": "https://g/3"},
            }
        },
        {  # no language at all, Russian letters
            "volumeInfo": {
                "title": "Мастер и Маргарита",
                "imageLinks": {"thumbnail": "https://g/4"},
            }
        },
    ]
}
OPEN_LIBRARY = {
    "docs": [
        {
            "title": "Dune",
            "language": ["eng", "rus"],
            "isbn": ["9785171234567", "9780441013593"],
            "cover_i": 1,
        },
        {"title": "Дюна", "language": ["rus"], "cover_i": 2},
    ]
}


@pytest.fixture
def catalogues(monkeypatch):
    monkeypatch.setattr(
        cover_sources, "_get_json", lambda url: GOOGLE if "googleapis" in url else OPEN_LIBRARY
    )
    monkeypatch.setattr(cover_sources, "google_key", lambda: "k")


def test_lookup_drops_russian_editions(catalogues):
    found = book_lookup.lookup_books("Дюна")
    assert [(b["title"], b["source"]) for b in found] == [
        ("Дюна", "Google Books"),
        ("Dune", "Open Library"),
    ]
    assert found[1]["isbn"] == "9780441013593"  # the Russian edition's ISBN is never offered


def test_cover_search_drops_russian_editions(catalogues):
    srcs = [c["src"] for c in cover_sources.search_covers("", query="Дюна")]
    assert srcs == ["https://g/1", "https://covers.openlibrary.org/b/id/1-L.jpg"]
