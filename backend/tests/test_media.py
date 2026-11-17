import pytest

from common.http import ValidationError
from conftest import body_of, make_event
from domain.book import Book
from domain.media import is_allowed_cover_url, is_own_photo_key, new_photo_key
from domain.profile import Profile
from handlers import my_books, uploads
from handlers import profile as profile_handler
from repositories.books import BookRepository
from repositories.profiles import ProfileRepository

BOOK = {
    "title": "Дюна",
    "author": "Френк Герберт",
    "language": "uk",
    "genre": "scifi",
    "offer": "give",
}
PROFILE = {"display_name": "Анна", "telegram": "anna_reads"}


@pytest.fixture(autouse=True)
def _repos(monkeypatch, table):
    monkeypatch.setattr(my_books, "get_repo", lambda: BookRepository(table))
    monkeypatch.setattr(profile_handler, "get_repo", lambda: ProfileRepository(table))


# ----- keys and urls -----


def test_photo_keys_are_scoped_to_the_owner():
    key = new_photo_key("cover", "user-1", "image/jpeg")
    assert key.startswith("covers/user-1/") and key.endswith(".jpg")
    assert is_own_photo_key(key, "cover", "user-1")
    assert not is_own_photo_key(key, "cover", "user-2")
    assert not is_own_photo_key(key, "avatar", "user-1")
    assert not is_own_photo_key("covers/user-1/../user-2/x.jpg", "cover", "user-1")


@pytest.mark.parametrize(
    "url, ok",
    [
        ("https://books.google.com/books/content?id=abc&printsec=frontcover&img=1&zoom=1", True),
        ("https://covers.openlibrary.org/b/id/12345-L.jpg", True),
        ("http://covers.openlibrary.org/b/id/12345-L.jpg", False),  # not https
        ("https://evil.example.com/cover.jpg", False),
        ("https://covers.openlibrary.org.evil.com/x.jpg", False),
        ("javascript:alert(1)", False),
    ],
)
def test_cover_url_allowlist(url, ok):
    assert is_allowed_cover_url(url) is ok


# ----- uploads endpoint -----


def test_upload_form_for_own_prefix():
    body = {"kind": "avatar", "content_type": "image/png"}
    result = body_of(uploads.handler(make_event(body=body), None))
    assert result["key"].startswith("avatars/user-1/") and result["key"].endswith(".png")
    assert result["url"] == "https://bucket.test/"


@pytest.mark.parametrize(
    "body",
    [
        {"kind": "cover", "content_type": "application/pdf"},
        {"kind": "x", "content_type": "image/jpeg"},
    ],
)
def test_upload_rejects_bad_input(body):
    assert uploads.handler(make_event(body=body), None)["statusCode"] == 400


# ----- books with covers -----


def test_book_cover_from_upload_or_search():
    key = new_photo_key("cover", "u", "image/jpeg")
    uploaded = Book.from_input("u", {**BOOK, "cover_key": key})
    assert uploaded.to_json()["cover_src"] == f"https://photos.test/{key}"

    found_url = "https://covers.openlibrary.org/b/id/1-L.jpg"
    found = Book.from_input("u", {**BOOK, "cover_url": found_url})
    assert found.to_json()["cover_src"] == found_url

    both = Book.from_input("u", {**BOOK, "cover_key": key, "cover_url": found_url})
    assert both.cover_url == ""  # uploaded photo wins

    assert Book.from_input("u", BOOK).to_json()["cover_src"] == ""


def test_book_cover_must_be_own_or_allowed():
    foreign = new_photo_key("cover", "someone-else", "image/jpeg")
    for data in ({"cover_key": foreign}, {"cover_url": "https://evil.example.com/x.jpg"}):
        with pytest.raises(ValidationError) as e:
            Book.from_input("u", {**BOOK, **data})
        assert "cover" in e.value.fields


def test_replacing_and_deleting_a_cover_removes_old_photos(fake_storage):
    first = new_photo_key("cover", "user-1", "image/jpeg")
    second = new_photo_key("cover", "user-1", "image/jpeg")
    book = body_of(my_books.create_handler(make_event(body={**BOOK, "cover_key": first}), None))[
        "book"
    ]

    path = {"id": book["book_id"]}
    my_books.update_handler(make_event(body={**BOOK, "cover_key": second}, path=path), None)
    assert fake_storage == [first]

    my_books.delete_handler(make_event(path=path), None)
    assert fake_storage == [first, second]


# ----- profile photo -----


def test_profile_avatar(fake_storage):
    key = new_photo_key("avatar", "user-1", "image/jpeg")
    saved = body_of(
        profile_handler.put_handler(make_event(body={**PROFILE, "avatar_key": key}), None)
    )
    assert saved["profile"]["avatar_src"] == f"https://photos.test/{key}"

    # a profile edit without avatar_key removes the photo and deletes the file
    profile_handler.put_handler(make_event(body=PROFILE), None)
    assert fake_storage == [key]


def test_avatar_must_be_own():
    foreign = new_photo_key("avatar", "someone-else", "image/jpeg")
    with pytest.raises(ValidationError) as e:
        Profile.from_input("user-1", "a@ucu.edu.ua", {**PROFILE, "avatar_key": foreign})
    assert "avatar_key" in e.value.fields
