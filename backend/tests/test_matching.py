import pytest

from conftest import body_of, make_event
from domain.book import Book
from domain.matching import (
    FOR_ME,
    FOR_THEM,
    MUTUAL,
    find_matches,
    satisfies,
    titles_match,
)
from domain.profile import Profile
from domain.wish import Wish
from handlers import matches as matches_handler
from handlers import users as users_handler
from repositories.books import BookRepository
from repositories.catalog import CatalogRepository
from repositories.profiles import ProfileRepository
from repositories.wishes import WishRepository


def book(owner, title, author="Автор", genre="classic", language="uk", offer="exchange"):
    data = {"title": title, "author": author, "genre": genre, "language": language, "offer": offer}
    return Book.from_input(owner, data)


def wish(owner, **data):
    return Wish.from_input(owner, data)


# ----- rules -----


@pytest.mark.parametrize(
    "wanted, offered, ok",
    [
        ("Дюна", "Дюна", True),
        ("дюна", "ДЮНА!", True),
        ("«Тіні забутих предків»", "Тіні забутих предків", True),
        ("Тіні забутих предків", "Тіні забутих предків. Intermezzo", True),  # contained
        ("Дюна", "Діти Дюни", False),  # short title must match exactly
        ("Місто", "Місто на краю", True),
        ("Гаррі Поттер", "Гаррі Поттер і філософський камінь", True),
        ("Кобзар", "Енеїда", False),
    ],
)
def test_titles_match(wanted, offered, ok):
    assert titles_match(wanted, offered) is ok


def test_book_wish_checks_author_surname_when_given():
    b = book("a", "Місто", "Валер’ян Підмогильний")
    assert satisfies(b, wish("me", kind="book", title="Місто", author="Підмогильний"))
    assert not satisfies(b, wish("me", kind="book", title="Місто", author="Іван Франко"))
    assert satisfies(b, wish("me", kind="book", title="Місто"))  # no author: title is enough


def test_genre_wish_and_language():
    b = book("a", "Dune", genre="scifi", language="en")
    assert satisfies(b, wish("me", kind="genre", genre="scifi")).by == "genre"
    assert satisfies(b, wish("me", kind="genre", genre="scifi", language="en"))
    assert not satisfies(b, wish("me", kind="genre", genre="scifi", language="uk"))
    assert not satisfies(b, wish("me", kind="genre", genre="fantasy"))


def test_own_books_never_match_own_wishes():
    assert not satisfies(book("me", "Дюна"), wish("me", kind="book", title="Дюна"))


# ----- grouping and ranking -----


def test_groups_and_order():
    books = [
        book("me", "Кобзар"),
        book("olia", "Дюна", genre="scifi"),  # I want it, she wants my Кобзар -> mutual
        book("petro", "Місто", offer="give"),  # I want it, free -> for_me
        book("ira", "Енеїда"),  # nobody wants it
    ]
    wishes = [
        wish("me", kind="book", title="Дюна"),
        wish("me", kind="book", title="Місто"),
        wish("olia", kind="book", title="Кобзар"),
        wish("ira", kind="genre", genre="classic"),  # wants my Кобзар (classic) -> for_them
    ]
    result = find_matches("me", books, wishes)
    assert [(m.user_id, m.kind) for m in result] == [
        ("olia", MUTUAL),
        ("petro", FOR_ME),
        ("ira", FOR_THEM),
    ]
    olia = result[0]
    assert [m.book.title for m in olia.they_have] == ["Дюна"]
    assert [m.book.title for m in olia.they_want] == ["Кобзар"]


def test_one_entry_per_book_with_the_strongest_reason():
    books = [book("olia", "Дюна", genre="scifi")]
    wishes = [
        wish("me", kind="genre", genre="scifi"),
        wish("me", kind="book", title="Дюна"),
    ]
    [match] = find_matches("me", books, wishes)
    assert len(match.they_have) == 1
    assert match.they_have[0].reason.by == "title"


def test_title_match_outranks_genre_match():
    books = [book("a", "Дюна", genre="scifi"), book("b", "Солярис", genre="scifi")]
    wishes = [wish("me", kind="book", title="Дюна"), wish("me", kind="genre", genre="scifi")]
    assert [m.user_id for m in find_matches("me", books, wishes)] == ["a", "b"]


def test_no_matches():
    assert find_matches("me", [book("a", "Кобзар")], []) == []


# ----- handlers -----


@pytest.fixture
def world(table, monkeypatch):
    monkeypatch.setattr(
        matches_handler,
        "get_repos",
        lambda: (CatalogRepository(table), ProfileRepository(table)),
    )
    monkeypatch.setattr(
        users_handler,
        "get_repos",
        lambda: (ProfileRepository(table), BookRepository(table), WishRepository(table)),
    )
    profiles, books, wishes = ProfileRepository(table), BookRepository(table), WishRepository(table)
    for uid, name in [("me", "Анна"), ("olia", "Оля")]:
        profiles.save(
            Profile.from_input(
                uid, f"{uid}@ucu.edu.ua", {"display_name": name, "telegram": f"{uid}_reads"}
            )
        )
    books.save(book("me", "Кобзар"))
    books.save(book("olia", "Дюна", genre="scifi", offer="give"))
    books.save(book("ghost", "Енеїда"))  # owner without a profile
    wishes.save(wish("me", kind="book", title="Дюна"))
    wishes.save(wish("me", kind="genre", genre="classic"))
    wishes.save(wish("olia", kind="book", title="Кобзар"))
    return table


def test_matches_endpoint(world):
    body = body_of(matches_handler.handler(make_event(sub="me"), None))
    assert (body["my_books"], body["my_wishes"]) == (1, 2)
    [m] = body["matches"]  # "ghost" has a matching classic book but no profile -> skipped
    assert m["kind"] == MUTUAL
    assert m["user"]["display_name"] == "Оля"
    assert "telegram" not in m["user"]  # contacts only on the profile page
    assert m["they_have"][0]["book"]["title"] == "Дюна"
    assert m["they_want"][0]["book"]["title"] == "Кобзар"


def test_user_profile_endpoint(world):
    event = make_event(sub="me", path={"id": "olia"})
    body = body_of(users_handler.handler(event, None))
    assert body["profile"]["telegram"] == "olia_reads"
    assert "created_at" not in body["profile"]
    assert [b["title"] for b in body["books"]] == ["Дюна"]
    assert [w["title"] for w in body["wishes"]] == ["Кобзар"]


def test_user_profile_not_found(world):
    resp = users_handler.handler(make_event(sub="me", path={"id": "ghost"}), None)
    assert resp["statusCode"] == 404
