import pytest

from common.http import ValidationError
from conftest import body_of, make_event
from domain.wish import Wish
from handlers import my_wishes
from repositories.wishes import WishRepository

BOOK_WISH = {"kind": "book", "title": "Майстер корабля", "author": "Юрій Яновський"}
GENRE_WISH = {"kind": "genre", "genre": "fantasy", "language": "en", "note": "щось легке"}


@pytest.fixture(autouse=True)
def _repo(monkeypatch, table):
    monkeypatch.setattr(my_wishes, "get_repo", lambda: WishRepository(table))


def _add(body, sub="user-1"):
    resp = my_wishes.create_handler(make_event(sub=sub, body=body), None)
    assert resp["statusCode"] == 200, resp
    return body_of(resp)["wish"]


def _errors(data):
    with pytest.raises(ValidationError) as e:
        Wish.from_input("u", data)
    return e.value.fields


def test_kind_required():
    assert "kind" in _errors({"title": "X"})


def test_book_wish_needs_title_only():
    assert "title" in _errors({"kind": "book"})
    w = Wish.from_input("u", {"kind": "book", "title": " Дюна "})
    assert (w.title, w.author, w.genre) == ("Дюна", "", "")


def test_genre_wish_needs_genre_and_drops_title():
    assert "genre" in _errors({"kind": "genre"})
    w = Wish.from_input("u", {**GENRE_WISH, "title": "ignored"})
    assert (w.genre, w.language, w.title) == ("fantasy", "en", "")


@pytest.mark.parametrize(
    "data, field",
    [
        ({**GENRE_WISH, "genre": "cooking"}, "genre"),
        ({**GENRE_WISH, "language": "xx"}, "language"),
        ({**GENRE_WISH, "note": "x" * 301}, "note"),
    ],
)
def test_invalid(data, field):
    assert field in _errors(data)


def test_item_is_indexed_for_matching():
    item = Wish.from_input("u", BOOK_WISH).to_item()
    assert item["sk"].startswith("WISH#") and item["gsi1pk"] == "WISH"


def test_crud_flow():
    a = _add(BOOK_WISH)
    b = _add(GENRE_WISH)
    wishes = body_of(my_wishes.list_handler(make_event(), None))["wishes"]
    assert {w["wish_id"] for w in wishes} == {a["wish_id"], b["wish_id"]}

    event = make_event(body={**GENRE_WISH, "language": ""}, path={"id": b["wish_id"]})
    updated = body_of(my_wishes.update_handler(event, None))["wish"]
    assert updated["language"] == ""

    my_wishes.delete_handler(make_event(path={"id": a["wish_id"]}), None)
    wishes = body_of(my_wishes.list_handler(make_event(), None))["wishes"]
    assert [w["wish_id"] for w in wishes] == [b["wish_id"]]


def test_wishes_and_books_do_not_mix(table):
    from handlers import my_books
    from repositories.books import BookRepository

    _add(BOOK_WISH)
    books = BookRepository(table).list_by_owner("user-1")
    assert books == []
    assert my_books  # imported only to show the two collections share a table


def test_cannot_touch_someone_elses_wish():
    theirs = _add(BOOK_WISH, sub="other")
    resp = my_wishes.delete_handler(make_event(path={"id": theirs["wish_id"]}), None)
    assert resp["statusCode"] == 404
