import pytest

from conftest import body_of, make_event
from domain.ban import Ban
from domain.book import Book
from domain.profile import Profile
from domain.report import Report
from domain.wish import Wish
from handlers import profile, users
from repositories.account import AccountRepository
from repositories.books import BookRepository
from repositories.moderation import BanRepository, BlockRepository, ReportRepository
from repositories.profiles import ProfileRepository
from repositories.wishes import WishRepository

BOOK = {"title": "Dune", "author": "Herbert", "genre": "scifi", "language": "en", "offer": "give"}


def _profile(uid, **data):
    return Profile.from_input(uid, f"{uid}@ucu.edu.ua", {"display_name": uid, **data})


# ----- what the public profile shows -----


def test_no_contacts_and_never_the_email_without_a_match():
    p = _profile("olia", telegram="olia_reads", phone="0971234567", show_phone=True)
    data = p.to_public_json()
    assert (data["telegram"], data["phone"], data["contacts_hidden"]) == ("", "", True)
    assert "email" not in data and "show_phone" not in data


def test_phone_only_when_shared():
    hidden = _profile("olia", telegram="olia_reads", phone="0971234567")
    assert hidden.to_public_json(with_contacts=True)["phone"] == ""
    assert hidden.to_public_json(with_contacts=True)["telegram"] == "olia_reads"
    shared = _profile("olia", telegram="olia_reads", phone="0971234567", show_phone=True)
    assert shared.to_public_json(with_contacts=True)["phone"] == "+380971234567"


def test_phone_is_shared_when_it_is_the_only_contact():
    only_phone = _profile("olia", phone="0971234567")
    assert only_phone.to_public_json(with_contacts=True)["phone"] == "+380971234567"


@pytest.fixture
def env(table, monkeypatch):
    repos = (ProfileRepository(table), BookRepository(table), WishRepository(table))
    monkeypatch.setattr(users, "get_repos", lambda: repos)
    monkeypatch.setattr(profile, "get_repo", lambda: repos[0])
    monkeypatch.setattr(profile, "get_account_repo", lambda: AccountRepository(table))
    repos[0].save(_profile("olia", telegram="olia_reads"))
    repos[0].save(_profile("me", telegram="me_reads"))
    repos[1].save(Book.from_input("olia", BOOK))
    return table


def _view(sub="me", target="olia"):
    return body_of(users.handler(make_event(sub=sub, path={"id": target}), None))["profile"]


def test_contacts_appear_once_there_is_a_match(env):
    assert _view()["telegram"] == ""
    WishRepository(env).save(Wish.from_input("me", {"kind": "book", "title": "Dune"}))
    assert _view()["telegram"] == "olia_reads"  # I want her book
    assert _view(sub="olia", target="me")["telegram"] == "me_reads"  # and she sees me too


# ----- deleting the account -----


def test_delete_account_removes_everything_of_mine(env, fake_storage):
    p = ProfileRepository(env)
    me = _profile(
        "me", telegram="me_reads", avatar_key="avatars/me/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpg"
    )
    p.save(me)
    BookRepository(env).save(
        Book.from_input(
            "me", {**BOOK, "cover_key": "covers/me/cccccccccccccccccccccccccccccccc.jpg"}
        )
    )
    WishRepository(env).save(Wish.from_input("me", {"kind": "genre", "genre": "scifi"}))
    blocks = BlockRepository(env)
    blocks.block("me", "olia")
    blocks.block("x", "me")
    report = Report.from_input(
        "olia", "olia@ucu.edu.ua", {"target_type": "user", "target_id": "me", "reason": "spam"}
    )
    report.owner_id = "me"
    ReportRepository(env).save(report)

    resp = profile.delete_handler(make_event(sub="me"), None)
    assert resp["statusCode"] == 200
    assert not [k for k in env.items if k[0] == "USER#me"]
    assert not [k for k in env.items if k[1] in ("BLOCKEDBY#me", "BLOCK#me")]
    assert ReportRepository(env).open_reports() == []
    assert {
        "avatars/me/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpg",
        "covers/me/cccccccccccccccccccccccccccccccc.jpg",
    } <= set(fake_storage)
    assert ProfileRepository(env).get("olia")  # other students are untouched


def test_banned_student_cannot_delete_the_account(env):
    BanRepository(env).save(Ban.create("me", "mod"))
    assert profile.delete_handler(make_event(sub="me"), None)["statusCode"] == 403
    assert ProfileRepository(env).get("me")
