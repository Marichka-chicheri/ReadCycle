import pytest

from common.http import ValidationError
from conftest import body_of, make_event
from domain.profile import Profile, normalize_phone, normalize_telegram
from handlers import profile as profile_handler
from repositories.profiles import ProfileRepository

VALID = {"display_name": "Анна", "telegram": "@anna_reads"}


@pytest.fixture(autouse=True)
def _repo(monkeypatch, table):
    monkeypatch.setattr(profile_handler, "get_repo", lambda: ProfileRepository(table))


# ----- normalisation -----


@pytest.mark.parametrize(
    "raw, expected",
    [("@Anna_K", "Anna_K"), ("https://t.me/Anna_K", "Anna_K"), ("t.me/Anna_K", "Anna_K")],
)
def test_normalize_telegram(raw, expected):
    assert normalize_telegram(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("097 123 45 67", "+380971234567"),
        ("(097)123-45-67", "+380971234567"),
        ("380971234567", "+380971234567"),
        ("+48 601 234 567", "+48601234567"),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


# ----- validation -----


def _errors(data):
    with pytest.raises(ValidationError) as e:
        Profile.from_input("u", "a@ucu.edu.ua", data)
    return e.value.fields


def test_name_required():
    assert "display_name" in _errors({"telegram": "anna_reads"})


def test_at_least_one_contact_required():
    assert "contacts" in _errors({"display_name": "Анна"})


def test_phone_alone_is_enough():
    p = Profile.from_input("u", "a@ucu.edu.ua", {"display_name": "Анна", "phone": "0971234567"})
    assert p.phone == "+380971234567"
    assert p.telegram == ""


@pytest.mark.parametrize(
    "field, value",
    [
        ("telegram", "a b"),
        ("phone", "12345"),
        ("age", 7),
        ("age", "abc"),
        ("about", "x" * 601),
        ("favorite_genres", ["not-a-genre"]),
    ],
)
def test_invalid_fields(field, value):
    assert field in _errors({**VALID, field: value})


def test_optional_fields_and_genre_dedupe():
    p = Profile.from_input(
        "u",
        "a@ucu.edu.ua",
        {**VALID, "age": "20", "about": "  люблю фентезі ", "favorite_genres": ["fantasy"] * 2},
    )
    assert (p.age, p.about, p.favorite_genres) == (20, "люблю фентезі", ["fantasy"])


def test_dynamodb_round_trip():
    p = Profile.from_input("u", "a@ucu.edu.ua", {**VALID, "age": 19})
    item = p.to_item()
    assert (item["pk"], item["sk"]) == ("USER#u", "PROFILE")
    assert Profile.from_item(item) == p


# ----- handlers -----


def test_get_before_onboarding_returns_null():
    resp = profile_handler.get_handler(make_event(), None)
    assert resp["statusCode"] == 200
    assert body_of(resp) == {"profile": None}


def test_put_then_get(table):
    resp = profile_handler.put_handler(make_event(body=VALID), None)
    assert resp["statusCode"] == 200
    saved = body_of(resp)["profile"]
    assert saved["display_name"] == "Анна"
    assert saved["telegram"] == "anna_reads"
    assert saved["email"] == "anna@ucu.edu.ua"  # taken from the token, not the body

    got = body_of(profile_handler.get_handler(make_event(), None))["profile"]
    assert got == saved


def test_update_keeps_created_at(table):
    first = body_of(profile_handler.put_handler(make_event(body=VALID), None))["profile"]
    second = body_of(
        profile_handler.put_handler(make_event(body={**VALID, "display_name": "Аня"}), None)
    )["profile"]
    assert second["display_name"] == "Аня"
    assert second["created_at"] == first["created_at"]


def test_email_in_body_is_ignored():
    body = {**VALID, "email": "hacker@gmail.com"}
    saved = body_of(profile_handler.put_handler(make_event(body=body), None))["profile"]
    assert saved["email"] == "anna@ucu.edu.ua"


def test_validation_error_format():
    resp = profile_handler.put_handler(make_event(body={"display_name": "A"}), None)
    assert resp["statusCode"] == 400
    err = body_of(resp)["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert set(err["fields"]) >= {"display_name", "contacts"}


def test_bad_json():
    event = make_event()
    event["body"] = "{not json"
    resp = profile_handler.put_handler(event, None)
    assert resp["statusCode"] == 400
    assert body_of(resp)["error"]["code"] == "BAD_JSON"


def test_requires_token():
    resp = profile_handler.get_handler({}, None)
    assert resp["statusCode"] == 401
