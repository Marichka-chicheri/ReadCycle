import pytest

from common.http import ValidationError
from conftest import body_of, make_event
from domain.book import Book
from domain.catalog import CatalogFilter
from domain.profile import Profile
from handlers import catalog
from repositories.books import BookRepository
from repositories.catalog import CatalogRepository
from repositories.profiles import ProfileRepository


def _book(owner, title, author="Автор", genre="classic", language="uk", offer="exchange"):
    data = {"title": title, "author": author, "genre": genre, "language": language, "offer": offer}
    return Book.from_input(owner, data)


@pytest.fixture
def shelf(table, monkeypatch):
    monkeypatch.setattr(
        catalog, "get_repos", lambda: (CatalogRepository(table), ProfileRepository(table))
    )
    profiles = ProfileRepository(table)
    profiles.save(
        Profile.from_input("olia", "o@ucu.edu.ua", {"display_name": "Оля", "phone": "0971234567"})
    )
    books = BookRepository(table)
    for b in [
        _book("me", "Моя власна книга"),
        _book("olia", "Тіні забутих предків", "Михайло Коцюбинський"),
        _book("olia", "Dune", "Frank Herbert", genre="scifi", language="en", offer="give"),
        _book("nobody", "Кайдашева сім’я", "Іван Нечуй-Левицький"),
    ]:
        books.save(b)
    return table


def _search(**params):
    event = make_event(sub="me")
    event["queryStringParameters"] = params or None
    resp = catalog.list_handler(event, None)
    assert resp["statusCode"] == 200, resp
    return body_of(resp)


def test_shows_other_peoples_books_with_owner_names(shelf):
    result = _search()
    titles = {b["title"] for b in result["books"]}
    assert "Моя власна книга" not in titles
    assert titles == {"Тіні забутих предків", "Dune", "Кайдашева сім’я"}
    owners = {b["title"]: b["owner_name"] for b in result["books"]}
    assert owners["Dune"] == "Оля"
    assert owners["Кайдашева сім’я"] == "Студент УКУ"  # owner without a profile
    assert result["total"] == 3


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"genre": "scifi"}, {"Dune"}),
        ({"language": "uk"}, {"Тіні забутих предків", "Кайдашева сім’я"}),
        ({"offer": "give"}, {"Dune"}),
        ({"q": "коцюбинський тіні"}, {"Тіні забутих предків"}),
        ({"q": "КАЙДАШЕВА СІМ'Я"}, {"Кайдашева сім’я"}),  # apostrophe-insensitive
        ({"q": "herbert", "offer": "exchange"}, set()),
    ],
)
def test_filters(shelf, params, expected):
    assert {b["title"] for b in _search(**params)["books"]} == expected


def test_newest_first(table, monkeypatch):
    monkeypatch.setattr(
        catalog, "get_repos", lambda: (CatalogRepository(table), ProfileRepository(table))
    )
    old = _book("a", "Old")
    old.created_at, old.updated_at = "2026-01-01T00:00:00.000+00:00", ""
    new = _book("a", "New")
    BookRepository(table).save(old)
    BookRepository(table).save(new)
    assert [b["title"] for b in _search()["books"]] == ["New", "Old"]


@pytest.mark.parametrize("params", [{"genre": "cooking"}, {"language": "xx"}, {"offer": "sell"}])
def test_bad_filter(params):
    with pytest.raises(ValidationError):
        CatalogFilter.from_query(params)
