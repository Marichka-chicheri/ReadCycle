import pytest

from handlers import pre_signup


def _event(email):
    return {"triggerSource": "PreSignUp_SignUp", "request": {"userAttributes": {"email": email}}}


@pytest.fixture(autouse=True)
def _domain(monkeypatch):
    monkeypatch.setenv("ALLOWED_EMAIL_DOMAIN", "ucu.edu.ua")


@pytest.mark.parametrize("email", ["student@ucu.edu.ua", "Student.Name@UCU.EDU.UA"])
def test_ucu_email_allowed(email):
    event = _event(email)
    assert pre_signup.handler(event, None) is event


@pytest.mark.parametrize(
    "email",
    [
        "someone@gmail.com",
        "x@ucu.edu.ua.evil.com",
        "x@fake-ucu.edu.ua",
        "x@sub.ucu.edu.ua",
        "a@b@ucu.edu.ua",
        "",
    ],
)
def test_other_emails_rejected(email):
    with pytest.raises(Exception, match=pre_signup.ERROR_CODE):
        pre_signup.handler(_event(email), None)


def test_banned_email_cannot_sign_up_again(table, monkeypatch):
    from common import db
    from domain.ban import Ban
    from repositories.moderation import BanRepository

    monkeypatch.setenv("TABLE_NAME", "test")
    monkeypatch.setattr(db, "main_table", lambda: table)
    bans = BanRepository(table)
    bans.save(Ban.create("old-id", "mod@ucu.edu.ua", "spam", "Bad@UCU.edu.ua"))

    with pytest.raises(Exception, match=pre_signup.BANNED_CODE):
        pre_signup.handler(_event("bad@ucu.edu.ua"), None)
    assert pre_signup.handler(_event("good@ucu.edu.ua"), None)

    bans.delete("old-id")  # unbanned: may sign up again
    assert pre_signup.handler(_event("bad@ucu.edu.ua"), None)
