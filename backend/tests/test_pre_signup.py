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


# ---------- Sign in with Google ----------


class FakeCognito:
    """Records link calls; list_users answers from a fixed list."""

    def __init__(self, users):
        self.users = users
        self.filters = []
        self.links = []

    def list_users(self, UserPoolId, Filter, Limit):
        self.filters.append(Filter)
        return {"Users": self.users}

    def admin_link_provider_for_user(self, **kwargs):
        self.links.append(kwargs)


def _google_event(email="anna@ucu.edu.ua", verified="true", trigger="PreSignUp_ExternalProvider"):
    return {
        "triggerSource": trigger,
        "userPoolId": "eu-central-1_pool",
        "userName": "Google_1234567890",
        "request": {"userAttributes": {"email": email, "email_verified": verified}},
    }


@pytest.fixture
def google_on(monkeypatch):
    monkeypatch.setenv("GOOGLE_SIGNIN", "1")


def _fake_cognito(monkeypatch, users):
    fake = FakeCognito(users)
    monkeypatch.setattr(pre_signup, "_cognito", lambda: fake)
    return fake


def test_google_login_links_to_existing_email_account(google_on, monkeypatch):
    fake = _fake_cognito(monkeypatch, [{"Username": "native-uuid", "UserStatus": "CONFIRMED"}])
    event = _google_event()
    assert pre_signup.handler(event, None) is event
    assert len(fake.links) == 1
    link = fake.links[0]
    assert link["UserPoolId"] == "eu-central-1_pool"
    assert link["DestinationUser"] == {
        "ProviderName": "Cognito",
        "ProviderAttributeValue": "native-uuid",
    }
    assert link["SourceUser"] == {
        "ProviderName": "Google",
        "ProviderAttributeName": "Cognito_Subject",
        "ProviderAttributeValue": "1234567890",
    }


def test_google_login_without_existing_account_creates_new_user(google_on, monkeypatch):
    fake = _fake_cognito(monkeypatch, [])
    assert pre_signup.handler(_google_event(), None)
    assert fake.links == []


def test_google_login_ignores_unconfirmed_accounts(google_on, monkeypatch):
    fake = _fake_cognito(monkeypatch, [{"Username": "u", "UserStatus": "UNCONFIRMED"}])
    assert pre_signup.handler(_google_event(), None)
    assert fake.links == []


def test_google_non_ucu_email_rejected(google_on, monkeypatch):
    fake = _fake_cognito(monkeypatch, [])
    with pytest.raises(Exception, match=pre_signup.ERROR_CODE):
        pre_signup.handler(_google_event(email="someone@gmail.com"), None)
    assert fake.links == []


def test_google_unverified_email_rejected_and_never_linked(google_on, monkeypatch):
    # An unverified Google address could belong to anyone: linking would hand them the account.
    fake = _fake_cognito(monkeypatch, [{"Username": "u", "UserStatus": "CONFIRMED"}])
    with pytest.raises(Exception, match=pre_signup.NOT_VERIFIED_CODE):
        pre_signup.handler(_google_event(verified="false"), None)
    assert fake.links == []


def test_google_banned_email_rejected(google_on, table, monkeypatch):
    from common import db
    from domain.ban import Ban
    from repositories.moderation import BanRepository

    monkeypatch.setenv("TABLE_NAME", "test")
    monkeypatch.setattr(db, "main_table", lambda: table)
    BanRepository(table).save(Ban.create("old-id", "mod@ucu.edu.ua", "spam", "bad@ucu.edu.ua"))
    fake = _fake_cognito(monkeypatch, [])
    with pytest.raises(Exception, match=pre_signup.BANNED_CODE):
        pre_signup.handler(_google_event(email="bad@ucu.edu.ua"), None)
    assert fake.links == []


def test_password_signup_blocked_when_email_already_uses_google(google_on, monkeypatch):
    _fake_cognito(monkeypatch, [{"Username": "Google_1", "UserStatus": "EXTERNAL_PROVIDER"}])
    event = _google_event(trigger="PreSignUp_SignUp")
    with pytest.raises(Exception, match=pre_signup.USES_GOOGLE_CODE):
        pre_signup.handler(event, None)


def test_password_signup_allowed_when_no_google_account(google_on, monkeypatch):
    _fake_cognito(monkeypatch, [])
    event = _google_event(trigger="PreSignUp_SignUp")
    assert pre_signup.handler(event, None) is event


def test_email_lookup_tries_original_and_lowercase_spelling(google_on, monkeypatch):
    fake = _fake_cognito(monkeypatch, [])
    pre_signup.handler(_google_event(email="Anna@UCU.edu.ua"), None)
    assert fake.filters == ['email = "Anna@UCU.edu.ua"', 'email = "anna@ucu.edu.ua"']


def test_google_off_never_touches_cognito(monkeypatch):
    monkeypatch.delenv("GOOGLE_SIGNIN", raising=False)

    def boom():
        raise AssertionError("Cognito must not be called when Google sign-in is off")

    monkeypatch.setattr(pre_signup, "_cognito", boom)
    event = _google_event()
    assert pre_signup.handler(event, None) is event
