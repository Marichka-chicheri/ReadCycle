import pytest

from common import book_lookup, cover_sources
from common.http import ValidationError
from conftest import body_of, make_event
from domain.book import Book
from domain.book_metadata import guess_genre, map_language, normalize_isbn
from handlers import book_lookup as lookup_handler

GOOGLE = {
    "items": [
        {
            "volumeInfo": {
                "title": "Емоційний інтелект",
                "subtitle": "Чому він може важити більше, ніж IQ",
                "authors": ["Деніел Гоулман"],
                "publishedDate": "2018-05",
                "language": "uk",
                "categories": ["Psychology"],
                "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9786177561438"}],
                "imageLinks": {"thumbnail": "http://books.google.com/books/content?id=x"},
            }
        }
    ]
}
OPEN_LIBRARY = {
    "docs": [
        {
            "title": "Emotional Intelligence",
            "author_name": ["Daniel Goleman"],
            "first_publish_year": 1995,
            "isbn": ["0553383714", "9780553383713"],
            "language": ["eng"],
            "subject": ["Emotions", "Psychology"],
            "cover_i": 7,
        },
        {"title": "No details at all"},
    ]
}


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def fake_get(url):
        seen.append(url)
        return GOOGLE if "googleapis" in url else OPEN_LIBRARY

    monkeypatch.setattr(cover_sources, "_get_json", fake_get)
    monkeypatch.setattr(cover_sources, "google_key", lambda: "k")
    return seen


@pytest.mark.parametrize(
    "categories, genre",
    [
        (["Psychology"], "psychology"),
        (["Fiction / Science Fiction / General"], "scifi"),
        (["Juvenile Fiction"], "children"),
        (["Fiction / Fantasy / Epic"], "fantasy"),
        (["Fiction"], "modern"),
        (["Social Science"], "nonfiction"),
        (["Comics & Graphic Novels"], "comics"),
        (["Cooking"], ""),
        ([], ""),
    ],
)
def test_guess_genre(categories, genre):
    assert guess_genre(categories) == genre


def test_language_and_isbn_helpers():
    assert map_language(["ukr"]) == "uk"
    assert map_language(["en"]) == "en"
    assert map_language(["jpn"]) == "other"
    assert map_language([]) == ""
    assert normalize_isbn("978-617-7561-43-8") == "9786177561438"
    assert normalize_isbn("0-553-38371-x") == "055338371X"
    assert normalize_isbn("12345") == ""


def test_lookup_by_text_fills_our_fields(calls):
    books = book_lookup.lookup_books("Емоційний інтелект")
    first = books[0]
    assert first["title"] == "Емоційний інтелект"  # subtitle dropped
    assert (first["author"], first["year"], first["language"], first["genre"]) == (
        "Деніел Гоулман",
        "2018",
        "uk",
        "psychology",
    )
    assert first["isbn"] == "9786177561438"
    assert first["cover_url"].startswith("https://")
    second = books[1]
    assert (second["language"], second["isbn"], second["year"]) == ("en", "9780553383713", "1995")
    assert books[-1]["title"] == "No details at all"  # no cover/genre -> last


def test_lookup_by_isbn_uses_isbn_queries(calls):
    book_lookup.lookup_books("978-617-7561-43-8")
    assert any("isbn%3A9786177561438" in u for u in calls)
    assert any("isbn=9786177561438" in u for u in calls)


def test_endpoint(calls):
    event = make_event()
    event["queryStringParameters"] = {"q": "Dune"}
    assert len(body_of(lookup_handler.handler(event, None))["books"]) == 3


BOOK = {
    "title": "Дюна",
    "author": "Френк Герберт",
    "language": "uk",
    "genre": "scifi",
    "offer": "give",
}


def test_book_year_and_isbn():
    b = Book.from_input("u", {**BOOK, "year": "2019", "isbn": "978-617-7561-43-8"})
    assert (b.year, b.isbn) == ("2019", "9786177561438")
    for field, value in [("year", "1200"), ("year", "20x9"), ("isbn", "123")]:
        with pytest.raises(ValidationError) as e:
            Book.from_input("u", {**BOOK, field: value})
        assert field in e.value.fields
