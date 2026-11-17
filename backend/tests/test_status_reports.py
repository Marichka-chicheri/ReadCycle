import pytest

from common.http import ValidationError
from conftest import body_of, make_event
from domain.book import Book
from domain.matching import find_matches
from domain.profile import Profile
from domain.wish import Wish
from handlers import catalog, reports, users
from repositories.books import BookRepository
from repositories.catalog import CatalogRepository
from repositories.moderation import ReportRepository
from repositories.profiles import ProfileRepository
from repositories.wishes import WishRepository

BOOK = {"title": "Dune", "author": "Herbert", "genre": "scifi", "language": "en", "offer": "give"}


def _book(owner, **extra):
    return Book.from_input(owner, {**BOOK, **extra})


def test_new_book_is_available():
    assert _book("a").status == "available"


def test_edit_keeps_status_unless_changed():
    given = _book("a", status="given")
    assert Book.from_input("a", BOOK, existing=given).status == "given"
    assert (
        Book.from_input("a", {**BOOK, "status": "available"}, existing=given).status == "available"
    )


@pytest.mark.parametrize("status", ["lost", "reserved"])
def test_bad_status(status):
    with pytest.raises(ValidationError):
        _book("a", status=status)


@pytest.mark.parametrize("old", [None, "reserved"])
def test_old_items_are_available(old):
    item = _book("a").to_item()
    if old:
        item["status"] = old
    else:
        del item["status"]
    assert Book.from_item(item).status == "available"


def test_given_books_leave_catalog_matching_and_public_profile(table, monkeypatch):
    monkeypatch.setattr(
        catalog, "get_repos", lambda: (CatalogRepository(table), ProfileRepository(table))
    )
    monkeypatch.setattr(
        users,
        "get_repos",
        lambda: (ProfileRepository(table), BookRepository(table), WishRepository(table)),
    )
    ProfileRepository(table).save(
        Profile.from_input("olia", "o@ucu.edu.ua", {"display_name": "Оля", "phone": "0971234567"})
    )
    books = BookRepository(table)
    kept = _book("olia", title="Kept")
    gone = _book("olia", title="Gone", status="given")
    books.save(kept)
    books.save(gone)

    resp = catalog.list_handler(make_event(sub="me"), None)
    assert {b["title"] for b in body_of(resp)["books"]} == {"Kept"}

    resp = users.handler(make_event(sub="me", path={"id": "olia"}), None)
    assert {b["title"] for b in body_of(resp)["books"]} == {"Kept"}

    wishes = [Wish.from_input("me", {"kind": "genre", "genre": "scifi"})]
    found = find_matches("me", [kept, gone], wishes)
    assert [m.book.title for m in found[0].they_have] == ["Kept"]
    assert find_matches("me", [gone], wishes) == []


# ----- complaints -----


@pytest.fixture
def report_env(table, monkeypatch):
    monkeypatch.setattr(
        reports,
        "get_repos",
        lambda: (BookRepository(table), ProfileRepository(table), ReportRepository(table)),
    )
    ProfileRepository(table).save(
        Profile.from_input("olia", "o@ucu.edu.ua", {"display_name": "Оля", "phone": "0971234567"})
    )
    book = _book("olia")
    BookRepository(table).save(book)
    return book


def _report(body):
    return reports.create_handler(make_event(sub="me", body=body), None)


def test_report_book(table, report_env):
    resp = _report(
        {
            "target_type": "book",
            "target_id": report_env.book_id,
            "owner_id": "olia",
            "reason": "spam",
        }
    )
    assert resp["statusCode"] == 200
    saved = table.items[(f"REPORT#book#{report_env.book_id}", "BY#me")]
    assert saved["owner_id"] == "olia" and saved["title"] == "Dune" and saved["gsi1pk"] == "REPORT"


def test_report_user_and_repeat_replaces(table, report_env):
    body = {"target_type": "user", "target_id": "olia", "reason": "scam"}
    assert _report(body)["statusCode"] == 200
    assert _report({**body, "reason": "spam"})["statusCode"] == 200
    reports_saved = [k for k in table.items if k[0].startswith("REPORT#")]
    assert len(reports_saved) == 1


@pytest.mark.parametrize(
    "body, status",
    [
        ({"target_type": "user", "target_id": "olia", "reason": "other"}, 400),  # needs a comment
        ({"target_type": "user", "target_id": "olia", "reason": "nope"}, 400),
        ({"target_type": "user", "target_id": "ghost", "reason": "spam"}, 404),
        ({"target_type": "book", "target_id": "x", "owner_id": "olia", "reason": "spam"}, 404),
        ({"target_type": "user", "target_id": "me", "reason": "spam"}, 404),
    ],
)
def test_report_rejected(report_env, body, status):
    assert _report(body)["statusCode"] == status


def test_cannot_report_yourself(table, report_env):
    body = {"target_type": "user", "target_id": "olia", "reason": "spam"}
    resp = reports.create_handler(make_event(sub="olia", body=body), None)
    assert resp["statusCode"] == 400


def test_reports_stay_out_of_catalog(table, report_env):
    _report({"target_type": "user", "target_id": "olia", "reason": "spam"})
    assert len(CatalogRepository(table).all_books()) == 1
