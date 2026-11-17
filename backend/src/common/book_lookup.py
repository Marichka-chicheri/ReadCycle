"""Book lookup for auto-filling the "add a book" form: by title/author text or by ISBN.

Uses the same catalogues and key as cover search (common/cover_sources.py) and returns ready
values for our form: title, author, year, isbn, language, genre, cover.
"""

from __future__ import annotations

import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from common import cover_sources as sources
from domain.book_metadata import guess_genre, map_language, normalize_isbn, year_of

PER_SOURCE = 8
MAX_RESULTS = 10


def _google(query: str) -> list[dict]:
    key = sources.google_key()
    if not key:
        return []
    params = urllib.parse.urlencode(
        {"q": query, "maxResults": PER_SOURCE, "printType": "books", "key": key}
    )
    data = sources._get_json(f"https://www.googleapis.com/books/v1/volumes?{params}")
    out = []
    for item in data.get("items", []):
        v = item.get("volumeInfo", {})
        if not v.get("title"):
            continue
        ids = {i.get("type"): i.get("identifier", "") for i in v.get("industryIdentifiers", [])}
        links = v.get("imageLinks") or {}
        cover = links.get("thumbnail") or links.get("smallThumbnail") or ""
        out.append(
            {
                "title": v["title"],  # without the subtitle: it is too long for a spine
                "author": ", ".join(v.get("authors", [])),
                "year": year_of(v.get("publishedDate")),
                "isbn": normalize_isbn(ids.get("ISBN_13") or ids.get("ISBN_10") or ""),
                "language": map_language([v.get("language", "")] if v.get("language") else []),
                "genre": guess_genre(v.get("categories", [])),
                "cover_url": cover.replace("http://", "https://", 1).replace("&edge=curl", ""),
                "source": "Google Books",
            }
        )
    return out


def _open_library(params: dict) -> list[dict]:
    fields = "title,author_name,first_publish_year,isbn,language,subject,cover_i"
    query = urllib.parse.urlencode({**params, "limit": PER_SOURCE, "fields": fields})
    data = sources._get_json(f"https://openlibrary.org/search.json?{query}")
    out = []
    for d in data.get("docs", []):
        if not d.get("title"):
            continue
        isbns = [normalize_isbn(i) for i in d.get("isbn", [])]
        out.append(
            {
                "title": d["title"],
                "author": ", ".join(d.get("author_name", [])[:3]),
                "year": year_of(d.get("first_publish_year")),
                "isbn": next((i for i in isbns if len(i) == 13), next(filter(None, isbns), "")),
                "language": map_language(d.get("language", [])),
                "genre": guess_genre(d.get("subject", [])[:15]),
                "cover_url": (
                    f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg"
                    if d.get("cover_i")
                    else ""
                ),
                "source": "Open Library",
            }
        )
    return out


def _safe(fn, arg) -> list[dict]:
    try:
        return fn(arg)
    except Exception as e:  # noqa: BLE001 - one failing source must not break the lookup
        sources.log.warning("book lookup source failed: %s", e)
        return []


def lookup_books(text: str) -> list[dict]:
    text = (text or "").strip()
    if not text:
        return []
    isbn = normalize_isbn(text)
    if isbn:
        tasks = [(_google, f"isbn:{isbn}"), (_open_library, {"isbn": isbn})]
    else:
        tasks = [(_google, text), (_open_library, {"q": text})]
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        batches = list(pool.map(lambda t: _safe(*t), tasks))

    # Interleave sources (Google first: better for Ukrainian books), drop near-duplicates.
    merged, seen = [], set()
    for i in range(max((len(b) for b in batches), default=0)):
        for batch in batches:
            if i < len(batch):
                item = batch[i]
                key = (item["title"].casefold(), item["author"].casefold(), item["year"])
                if key not in seen:
                    seen.add(key)
                    merged.append(item)
    # Entries with a cover and a known genre are the most useful for auto-fill.
    merged.sort(key=lambda b: (not b["cover_url"], not b["genre"]))
    return merged[:MAX_RESULTS]
