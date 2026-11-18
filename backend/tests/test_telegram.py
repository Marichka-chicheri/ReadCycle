import json

import pytest

from common import alerts, telegram
from conftest import body_of, make_event
from domain.book import Book
from domain.profile import Profile
from domain.wish import Wish
from handlers import my_books
from handlers import telegram as tg
from repositories.account import AccountRepository
from repositories.books import BookRepository
from repositories.moderation import BlockRepository
from repositories.profiles import ProfileRepository
from repositories.telegram import TelegramRepository
from repositories.wishes import WishRepository

BOOK = {"title": "Дюна", "author": "Френк Герберт", "genre": "scifi", "language": "uk"}


@pytest.fixture
def sent(table, monkeypatch):
    """Telegram is on; messages are recorded instead of sent; all repos use the fake table."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("SITE_URL", "https://readcycle.test")
    out = []
    monkeypatch.setattr(
        telegram, "send_message", lambda chat, text, button=None: out.append((chat, text, button))
    )
    monkeypatch.setattr(telegram, "bot_username", lambda: "ReadCycleBot")
    monkeypatch.setattr(tg, "get_repo", lambda: TelegramRepository(table))
    monkeypatch.setattr(alerts, "main_table", lambda: table)
    monkeypatch.setattr(my_books, "get_repo", lambda: BookRepository(table))
    for uid in ("olia", "me", "x"):
        ProfileRepository(table).save(
            Profile.from_input(
                uid,
                f"{uid}@ucu.edu.ua",
                {"display_name": f"{uid.title()} Reader", "telegram": f"{uid}_reads"},
            )
        )
    return out


def _update(text, chat_id=555, secret=None):
    event = {
        "headers": {"X-Telegram-Bot-Api-Secret-Token": secret or telegram.webhook_secret()},
        "body": json.dumps({"message": {"chat": {"id": chat_id, "type": "private"}, "text": text}}),
    }
    return tg.webhook_handler(event, None)


def _link(user="me", chat_id=555):
    url = body_of(tg.link_handler(make_event(sub=user), None))["url"]
    assert url.startswith("https://t.me/ReadCycleBot?start=")
    _update(f"/start {url.split('=', 1)[1]}", chat_id)


# ----- linking -----


def test_link_with_start_code(table, sent):
    assert body_of(tg.status_handler(make_event(sub="me"), None)) == {
        "available": True,
        "linked": False,
    }
    _link()
    assert TelegramRepository(table).chat_id("me") == "555"
    assert body_of(tg.status_handler(make_event(sub="me"), None))["linked"] is True
    assert "Готово" in sent[-1][1]


def test_code_works_once(table, sent):
    url = body_of(tg.link_handler(make_event(sub="me"), None))["url"]
    code = url.split("=", 1)[1]
    _update(f"/start {code}", 1)
    _update(f"/start {code}", 2)  # someone else trying the same link
    assert TelegramRepository(table).chat_id("me") == "1"
    assert "застаріло" in sent[-1][1]


def test_webhook_needs_the_secret(table, sent):
    assert _update("/start x", secret="wrong")["statusCode"] == 403
    assert sent == []


def test_stop_and_unlink(table, sent):
    _link()
    _update("/stop")
    assert TelegramRepository(table).chat_id("me") is None
    _link()
    tg.unlink_handler(make_event(sub="me"), None)
    assert TelegramRepository(table).chat_id("me") is None


def test_bot_switched_off(table, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert body_of(tg.status_handler(make_event(), None))["available"] is False
    assert tg.link_handler(make_event(), None)["statusCode"] == 503


# ----- alerts about a new book -----


def test_new_book_alerts_wishers(table, sent):
    _link("me", 1)
    _link("x", 2)
    WishRepository(table).save(Wish.from_input("me", {"kind": "book", "title": "Дюна"}))
    WishRepository(table).save(Wish.from_input("x", {"kind": "genre", "genre": "scifi"}))
    WishRepository(table).save(Wish.from_input("olia", {"kind": "genre", "genre": "scifi"}))
    sent.clear()

    resp = my_books.create_handler(make_event(sub="olia", body={**BOOK, "offer": "give"}), None)
    assert resp["statusCode"] == 200
    by_chat = {chat: (text, button) for chat, text, button in sent}
    assert set(by_chat) == {"1", "2"}  # the owner herself is never alerted
    assert "з твого вішліста" in by_chat["1"][0] and "Дюна" in by_chat["1"][0]
    assert "Наукова фантастика" in by_chat["2"][0]
    assert by_chat["1"][1] == ("Відкрити на ReadCycle", "https://readcycle.test/u/olia")


def test_no_alerts_for_blocked_or_unlinked(table, sent):
    _link("me", 1)
    WishRepository(table).save(Wish.from_input("me", {"kind": "genre", "genre": "scifi"}))
    WishRepository(table).save(Wish.from_input("x", {"kind": "genre", "genre": "scifi"}))  # no bot
    BlockRepository(table).block("me", "olia")
    sent.clear()
    book = Book.from_input("olia", {**BOOK, "offer": "give"})
    assert alerts.notify_wishers(book) == 0
    assert sent == []


def test_alert_text_is_escaped():
    from domain.alerts import alert_text
    from domain.matching import satisfies

    book = Book.from_input("o", {**BOOK, "title": "<b>X</b>", "offer": "exchange"})
    reason = satisfies(book, Wish.from_input("me", {"kind": "book", "title": "<b>X</b>"}))
    text = alert_text(book, reason, "Оля & Co")
    assert "&lt;b&gt;X&lt;/b&gt;" in text and "Оля &amp; Co" in text


def test_deleting_account_forgets_the_chat(table, sent):
    _link("me", 7)
    AccountRepository(table).delete("me")
    assert ("TGCHAT#7", "LINK") not in table.items
