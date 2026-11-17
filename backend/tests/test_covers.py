import pytest

from common import cover_sources
from conftest import body_of, make_event
from handlers import covers

GOOGLE = {
    "items": [
        {
            "volumeInfo": {
                "title": "Емоційний інтелект",
                "authors": ["Деніел Гоулман"],
                "publishedDate": "2018-03-01",
                "imageLinks": {
                    "thumbnail": "http://books.google.com/books/content?id=g1&edge=curl"
                },
            }
        },
        {"volumeInfo": {"title": "No picture"}},
    ]
}
OPEN_LIBRARY = {
    "docs": [
        {"title": "Emotional Intelligence", "author_name": ["Daniel Goleman"], "cover_i": 42},
        {"title": "No cover"},
    ]
}


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def fake_get(url):
        seen.append(url)
        return GOOGLE if "googleapis" in url else OPEN_LIBRARY

    monkeypatch.setattr(cover_sources, "_get_json", fake_get)
    monkeypatch.setattr(cover_sources, "google_key", lambda: "test-key")
    return seen


def test_merges_both_sources_without_duplicates(calls):
    found = cover_sources.search_covers("Емоційний інтелект", "Гоулман")
    assert [c["src"] for c in found] == [
        "https://books.google.com/books/content?id=g1",  # https, no curl effect
        "https://covers.openlibrary.org/b/id/42-L.jpg",
    ]
    assert found[0]["year"] == "2018"
    assert len(calls) == 4  # 2 Google variants + 2 Open Library variants
    assert all("key=test-key" in u for u in calls if "googleapis" in u)


def test_free_text_query(calls):
    cover_sources.search_covers("", "", "Emotional Intelligence")
    assert len(calls) == 2


def test_works_without_google_key(calls, monkeypatch):
    monkeypatch.setattr(cover_sources, "google_key", lambda: "")
    found = cover_sources.search_covers("Dune")
    assert [c["source"] for c in found] == ["Open Library"]
    assert not any("googleapis" in u for u in calls)


def test_a_failing_source_does_not_break_search(monkeypatch):
    def flaky(url):
        if "googleapis" in url:
            raise TimeoutError("slow")
        return OPEN_LIBRARY

    monkeypatch.setattr(cover_sources, "_get_json", flaky)
    monkeypatch.setattr(cover_sources, "google_key", lambda: "k")
    assert len(cover_sources.search_covers("Dune")) == 1


def test_empty_title_returns_nothing(calls):
    assert cover_sources.search_covers("  ") == []
    assert calls == []


def test_endpoint(calls):
    event = make_event()
    event["queryStringParameters"] = {"title": "Емоційний інтелект", "author": "Гоулман"}
    body = body_of(covers.handler(event, None))
    assert body["google"] is True
    assert len(body["covers"]) == 2
