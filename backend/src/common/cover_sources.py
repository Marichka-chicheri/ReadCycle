"""Cover search in two free book catalogues, done from the backend.

- Google Books: the best coverage of Ukrainian books, but it needs an API key — anonymous
  requests share one worldwide quota that is almost always exhausted (HTTP 429). The key lives in
  SSM Parameter Store (GOOGLE_BOOKS_KEY_PARAM), never in the code.
- Open Library: no key, large covers, mostly English-language books.

Several query variants run in parallel; results are merged, de-duplicated, best first.
Only stdlib (urllib) is used, so the Lambda zip needs no extra packages.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from functools import cache

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 4
PER_QUERY = 20
MAX_RESULTS = 30


@cache
def google_key() -> str:
    """The Google Books API key from SSM, or "" if it is not configured."""
    name = os.environ.get("GOOGLE_BOOKS_KEY_PARAM", "")
    if not name:
        return ""
    try:
        import boto3

        ssm = boto3.client("ssm")
        return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"].strip()
    except Exception:  # noqa: BLE001 - search still works with Open Library alone
        log.warning("Google Books key %s is not available", name)
        return ""


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ReadCycle/1.0 (UCU student project)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:  # noqa: S310 - fixed hosts
        return json.loads(resp.read().decode("utf-8"))


def _google(query: str) -> list[dict]:
    key = google_key()
    if not key:
        return []
    params = urllib.parse.urlencode(
        {"q": query, "maxResults": PER_QUERY, "printType": "books", "key": key}
    )
    data = _get_json(f"https://www.googleapis.com/books/v1/volumes?{params}")
    out = []
    for item in data.get("items", []):
        v = item.get("volumeInfo", {})
        links = v.get("imageLinks") or {}
        link = links.get("thumbnail") or links.get("smallThumbnail")
        if not link:
            continue
        out.append(
            {
                "src": link.replace("http://", "https://", 1).replace("&edge=curl", ""),
                "title": v.get("title", ""),
                "author": ", ".join(v.get("authors", [])),
                "year": (v.get("publishedDate") or "")[:4],
                "source": "Google Books",
            }
        )
    return out


def _open_library(params: dict) -> list[dict]:
    query = urllib.parse.urlencode(
        {**params, "limit": PER_QUERY, "fields": "title,author_name,first_publish_year,cover_i"}
    )
    data = _get_json(f"https://openlibrary.org/search.json?{query}")
    return [
        {
            "src": f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg",
            "title": d.get("title", ""),
            "author": ", ".join(d.get("author_name", [])),
            "year": str(d.get("first_publish_year") or ""),
            "source": "Open Library",
        }
        for d in data.get("docs", [])
        if d.get("cover_i")
    ]


def _safe(fn, arg) -> list[dict]:
    try:
        return fn(arg)
    except Exception as e:  # noqa: BLE001 - one slow or failing source must not break search
        log.warning("cover source failed: %s", e)
        return []


def search_covers(title: str, author: str = "", query: str = "") -> list[dict]:
    """Covers for a book. `query` (free text) overrides title/author when given."""
    title, author, query = title.strip(), author.strip(), query.strip()
    if query:
        tasks = [(_google, query), (_open_library, {"q": query})]
    else:
        if not title:
            return []
        exact = f'intitle:"{title}"' + (f' inauthor:"{author}"' if author else "")
        both = f"{title} {author}".strip()
        tasks = [
            (_google, exact),
            (_google, both),
            (_open_library, {"q": both}),
            (_open_library, {"title": title}),
        ]
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        batches = list(pool.map(lambda t: _safe(*t), tasks))

    seen: set[str] = set()
    merged: list[dict] = []
    for batch in batches:  # order of `tasks` = order of relevance
        for cover in batch:
            if cover["src"] not in seen:
                seen.add(cover["src"])
                merged.append(cover)
    return merged[:MAX_RESULTS]
