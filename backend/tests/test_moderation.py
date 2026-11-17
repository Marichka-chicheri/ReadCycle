import pytest

from common.http import ApiError
from common.moderation import assert_not_banned
from conftest import body_of, make_event
from domain.ban import Ban
from domain.book import Book
from domain.profile import Profile
from domain.report import AUTO_BAN_COMPLAINANTS, MAX_REPORTS_PER_DAY
from domain.wish import Wish
from handlers import blocks, catalog, matches, moderator, my_books, profile, reports, users
from repositories.books import BookRepository
from repositories.catalog import CatalogRepository
from repositories.moderation import BanRepository, BlockRepository, ReportRepository
from repositories.profiles import ProfileRepository
from repositories.wishes import WishRepository

BOOK = {"title": "Dune", "author": "Herbert", "genre": "scifi", "language": "en", "offer": "give"}
MOD = "mod@ucu.edu.ua"
USERS = ("olia", "me", "bad", "x1", "x2", "x3", "x4", "x5", "x6")


@pytest.fixture
def env(table, monkeypatch):
    monkeypatch.setenv("MODERATOR_EMAILS", f" {MOD.upper()} , other@ucu.edu.ua")
    book_repo, profile_repo = BookRepository(table), ProfileRepository(table)
    report_repo, ban_repo = ReportRepository(table), BanRepository(table)
    monkeypatch.setattr(reports, "get_repos", lambda: (book_repo, profile_repo, report_repo))
    monkeypatch.setattr(blocks, "get_repos", lambda: (BlockRepository(table), profile_repo))
    monkeypatch.setattr(
        moderator, "get_repos", lambda: (report_repo, ban_repo, book_repo, profile_repo)
    )
    monkeypatch.setattr(catalog, "get_repos", lambda: (CatalogRepository(table), profile_repo))
    monkeypatch.setattr(matches, "get_repos", lambda: (CatalogRepository(table), profile_repo))
    monkeypatch.setattr(
        users, "get_repos", lambda: (profile_repo, book_repo, WishRepository(table))
    )
    monkeypatch.setattr(profile, "get_repo", lambda: profile_repo)
    for uid in USERS:
        data = {"display_name": uid, "phone": "0971234567"}
        profile_repo.save(Profile.from_input(uid, f"{uid}@ucu.edu.ua", data))
    book_repo.save(Book.from_input("bad", BOOK))
    return table


def call(handler, sub="me", email=None, body=None, path=None):
    event = make_event(sub=sub, email=email or f"{sub}@ucu.edu.ua", body=body, path=path)
    resp = handler(event, None)
    return resp["statusCode"], body_of(resp)


def report(sub, target="bad", reason="spam", **extra):
    body = {"target_type": "user", "target_id": target, "reason": reason, **extra}
    return call(reports.create_handler, sub=sub, body=body)


# ----- complaint limits and automatic suspension -----


def test_daily_limit(env):
    assert MAX_REPORTS_PER_DAY == 5
    for target in ("olia", "x1", "x2", "x3", "x4"):
        assert report("me", target)[0] == 200
    status, body = report("me", "x5")
    assert status == 429 and body["error"]["code"] == "TOO_MANY_REPORTS"


def test_enough_different_students_suspend_the_account(env):
    for uid in ("x1", "x2", "x3")[: AUTO_BAN_COMPLAINANTS - 1]:
        report(uid)
    assert BanRepository(env).get("bad") is None
    report("x3")
    ban = BanRepository(env).get("bad")
    assert ban and ban.banned_by == "auto"


def test_same_student_complaining_twice_does_not_add_up(env):
    for _ in range(AUTO_BAN_COMPLAINANTS + 1):
        report("x1")
    assert BanRepository(env).get("bad") is None


def test_book_complaints_count_towards_the_owner(env):
    book_id = BookRepository(env).list_by_owner("bad")[0].book_id
    for uid in ("x1", "x2", "x3"):
        body = {"target_type": "book", "target_id": book_id, "owner_id": "bad", "reason": "spam"}
        assert call(reports.create_handler, sub=uid, body=body)[0] == 200
    assert BanRepository(env).get("bad")


# ----- what a ban does -----


def test_banned_account_is_hidden_and_read_only(env):
    BanRepository(env).save(Ban.create("bad", "auto", "x"))
    assert call(catalog.list_handler)[1]["books"] == []
    assert call(users.handler, path={"id": "bad"})[0] == 404
    status, body = call(my_books.create_handler, sub="bad", body={**BOOK, "title": "New"})
    assert status == 403 and body["error"]["code"] == "ACCOUNT_BANNED"
    assert report("bad", "olia")[0] == 403
    with pytest.raises(ApiError):
        assert_not_banned("bad")


def test_banned_user_sees_the_flag_on_profile(env):
    BanRepository(env).save(Ban.create("bad", "auto"))
    assert call(profile.get_handler, sub="bad")[1]["banned"] is True
    assert call(profile.get_handler)[1]["banned"] is False


def test_matches_skip_banned_accounts(env):
    WishRepository(env).save(Wish.from_input("me", {"kind": "genre", "genre": "scifi"}))
    assert len(call(matches.handler)[1]["matches"]) == 1
    BanRepository(env).save(Ban.create("bad", "auto"))
    assert call(matches.handler)[1]["matches"] == []


# ----- blocking another student -----


def test_block_hides_both_ways_and_unblock_restores(env):
    assert call(blocks.block_handler, path={"id": "bad"})[0] == 200
    assert call(catalog.list_handler)[1]["books"] == []
    assert call(users.handler, path={"id": "bad"})[0] == 404
    assert call(users.handler, sub="bad", path={"id": "me"})[0] == 404  # and the other way round
    listed = call(blocks.list_handler)[1]["blocks"]
    assert listed == [{"user_id": "bad", "display_name": "bad"}]
    assert call(blocks.list_handler, sub="bad")[1]["blocks"] == []  # they cannot see who blocked

    call(blocks.unblock_handler, path={"id": "bad"})
    assert len(call(catalog.list_handler)[1]["books"]) == 1
    assert call(users.handler, sub="bad", path={"id": "me"})[0] == 200


def test_cannot_block_yourself_or_a_ghost(env):
    assert call(blocks.block_handler, path={"id": "me"})[0] == 400
    assert call(blocks.block_handler, path={"id": "ghost"})[0] == 404


# ----- moderator page -----


def _mod(handler, **kw):
    return call(handler, sub="m", email=MOD, **kw)


def test_only_moderators_get_in(env):
    for handler in (moderator.reports_handler, moderator.bans_handler):
        assert call(handler, sub="me")[0] == 403
    assert _mod(moderator.reports_handler)[0] == 200
    assert _mod(profile.get_handler)[1]["moderator"] is True
    assert call(profile.get_handler)[1]["moderator"] is False


def test_reports_are_grouped_and_dismiss_forgets_them(env):
    report("x1", reason="other", comment="rude")
    report("x2", reason="scam")
    group = _mod(moderator.reports_handler)[1]["groups"][0]
    assert (group["target_id"], group["count"], group["owner_name"]) == ("bad", 2, "bad")
    assert {r["reason"] for r in group["reports"]} == {"other", "scam"}

    body = {"target_type": "user", "target_id": "bad", "action": "dismiss"}
    assert _mod(moderator.resolve_handler, body=body)[0] == 200
    assert _mod(moderator.reports_handler)[1]["groups"] == []
    report("x3")  # dismissed complaints must not add up to an automatic ban later
    assert BanRepository(env).get("bad") is None


def test_moderator_removes_book_or_bans_user(env):
    book_id = BookRepository(env).list_by_owner("bad")[0].book_id
    body = {"target_type": "book", "target_id": book_id, "owner_id": "bad", "reason": "spam"}
    call(reports.create_handler, sub="x1", body=body)
    resolve = {"target_type": "book", "target_id": book_id, "action": "remove_book"}
    assert _mod(moderator.resolve_handler, body=resolve)[0] == 200
    assert BookRepository(env).list_by_owner("bad") == []
    assert _mod(moderator.reports_handler)[1]["groups"] == []

    report("x1")
    resolve = {"target_type": "user", "target_id": "bad", "action": "ban_user"}
    assert _mod(moderator.resolve_handler, body=resolve)[0] == 200
    assert BanRepository(env).get("bad").banned_by == MOD


def test_bad_resolve_requests(env):
    report("x1")
    body = {"target_type": "user", "target_id": "bad", "action": "remove_book"}
    assert _mod(moderator.resolve_handler, body=body)[0] == 400
    body["action"] = "explode"
    assert _mod(moderator.resolve_handler, body=body)[0] == 400


def test_ban_list_ban_and_unban(env):
    assert _mod(moderator.ban_handler, path={"id": "bad"}, body={"reason": "scam"})[0] == 200
    bans = _mod(moderator.bans_handler)[1]["bans"]
    assert [(b["user_id"], b["reason"], b["auto"]) for b in bans] == [("bad", "scam", False)]
    assert _mod(moderator.ban_handler, path={"id": "ghost"})[0] == 404
    assert call(moderator.ban_handler, sub="me", path={"id": "bad"})[0] == 403

    assert _mod(moderator.unban_handler, path={"id": "bad"})[0] == 200
    assert BanRepository(env).get("bad") is None
    assert len(call(catalog.list_handler)[1]["books"]) == 1
