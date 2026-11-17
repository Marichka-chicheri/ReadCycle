import pytest

from common.http import ValidationError
from conftest import body_of, make_event
from domain.book import Book
from handlers import my_books
from repositories.books import BookRepository

BOOK = {
    "title": "Тіні забутих предків",
    "author": "Михайло Коцюбинський",
    "language": "uk",
    "genre": "classic",
    "offer": "exchange",
    "description": "  Гарний стан, з олівцевими нотатками ",
}


@pytest.fixture(autouse=True)
def _repo(monkeypatch, table):
    monkeypatch.setattr(my_books, "get_repo", lambda: BookRepository(table))


def _add(body=BOOK, sub="user-1"):
    return body_of(my_books.create_handler(make_event(sub=sub, body=body), None))["book"]


# ----- validation -----


@pytest.mark.parametrize(
    "field, value",
    [
        ("title", ""),
        ("author", " "),
        ("language", "klingon"),
        ("genre", ""),
        ("genre", "cooking"),
        ("offer", "sell"),
        ("description", "x" * 1001),
    ],
)
def test_invalid_fields(field, value):
    with pytest.raises(ValidationError) as e:
        Book.from_input("u", {**BOOK, field: value})
    assert field in e.value.fields


def test_book_is_normalised_and_indexed():
    book = Book.from_input("u", {**BOOK, "title": "  Тіні   забутих предків "})
    assert book.title == "Тіні забутих предків"
    assert book.description == "Гарний стан, з олівцевими нотатками"
    item = book.to_item()
    assert item["pk"] == "USER#u" and item["sk"] == f"BOOK#{book.book_id}"
    assert item["gsi1pk"] == "BOOK" and item["gsi1sk"].endswith(book.book_id)
    assert Book.from_item(item) == book


# ----- handlers -----


def test_add_and_list():
    added = _add()
    assert added["title"] == "Тіні забутих предків"
    listed = body_of(my_books.list_handler(make_event(), None))["books"]
    assert listed == [added]


def test_list_shows_only_own_books():
    _add(sub="someone-else")
    assert body_of(my_books.list_handler(make_event(), None))["books"] == []


def test_update_keeps_id_and_created_at():
    added = _add()
    event = make_event(body={**BOOK, "offer": "give"}, path={"id": added["book_id"]})
    updated = body_of(my_books.update_handler(event, None))["book"]
    assert updated["offer"] == "give"
    assert (updated["book_id"], updated["created_at"]) == (added["book_id"], added["created_at"])


def test_cannot_edit_or_delete_someone_elses_book():
    theirs = _add(sub="someone-else")
    path = {"id": theirs["book_id"]}
    assert my_books.update_handler(make_event(body=BOOK, path=path), None)["statusCode"] == 404
    assert my_books.delete_handler(make_event(path=path), None)["statusCode"] == 404


def test_delete():
    added = _add()
    resp = my_books.delete_handler(make_event(path={"id": added["book_id"]}), None)
    assert body_of(resp) == {"deleted": added["book_id"]}
    assert body_of(my_books.list_handler(make_event(), None))["books"] == []


def test_create_validation_error():
    resp = my_books.create_handler(make_event(body={"title": "X"}), None)
    assert resp["statusCode"] == 400
    assert {"author", "language", "genre", "offer"} <= set(body_of(resp)["error"]["fields"])


def test_limit(monkeypatch):
    monkeypatch.setattr(my_books.collection, "limit", 1)
    _add()
    resp = my_books.create_handler(make_event(body=BOOK), None)
    assert resp["statusCode"] == 400
    assert body_of(resp)["error"]["code"] == "LIMIT_REACHED"


def test_given_books_do_not_count_towards_the_limit(monkeypatch):
    monkeypatch.setattr(my_books.collection, "limit", 1)
    _add({**BOOK, "status": "given"})
    resp = my_books.create_handler(make_event(body=BOOK), None)
    assert resp["statusCode"] == 200
