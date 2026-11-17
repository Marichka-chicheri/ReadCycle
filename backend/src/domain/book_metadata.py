"""Turning catalogue metadata (Google Books, Open Library) into our own fields.

Catalogues describe books with free-form categories ("Fiction / Fantasy / Epic", "Psychology",
"Juvenile Fiction") and language codes ("uk", "ukr", "eng"). These helpers map them onto our
fixed genre and language lists; anything unknown maps to "" so the user picks it by hand.
"""

from __future__ import annotations

import re

# Most specific first: "Fiction / Science Fiction" must become scifi, not modern prose.
GENRE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("comics", ("comic", "graphic novel", "manga", "комікс")),
    ("young_adult", ("young adult",)),
    ("children", ("juvenile", "children", "picture book", "дитяч")),
    ("scifi", ("science fiction", "sci-fi", "dystop", "фантастик")),
    ("fantasy", ("fantasy", "magic", "фентез")),
    ("horror", ("horror", "жах")),
    ("thriller", ("thriller", "suspense", "трилер")),
    ("detective", ("mystery", "detective", "crime", "детектив")),
    ("romance", ("romance", "love stor", "любов")),
    ("historical", ("historical fiction", "історичн")),
    ("poetry", ("poetry", "poems", "поез", "вірш")),
    ("drama", ("drama", "plays", "п'єс", "драм")),
    ("biography", ("biography", "autobiography", "memoir", "біограф", "мемуар")),
    ("psychology", ("psychology", "психолог")),
    ("philosophy", ("philosophy", "філософ")),
    ("religion", ("religion", "christian", "bible", "theology", "релігі", "богослов")),
    ("business", ("business", "economics", "self-help", "personal growth", "бізнес")),
    ("nonfiction", ("social science", "political science", "essays", "nonfiction")),
    ("science", ("science", "mathematics", "technology", "computers", "наук")),
    ("history", ("history", "історі")),
    ("textbook", ("textbook", "study aids", "education", "підручник")),
    ("classic", ("classic", "класик")),
    ("modern", ("fiction", "novel", "literary", "роман", "проза")),
]

# ISO 639-1 (Google) and MARC / ISO 639-2 (Open Library) codes -> our language codes.
LANGUAGE_CODES = {
    "uk": "uk",
    "ukr": "uk",
    "en": "en",
    "eng": "en",
    "pl": "pl",
    "pol": "pl",
    "de": "de",
    "ger": "de",
    "deu": "de",
    "fr": "fr",
    "fre": "fr",
    "fra": "fr",
    "es": "es",
    "spa": "es",
    "it": "it",
    "ita": "it",
}

_ISBN_CHARS = re.compile(r"[\s\-]")


def guess_genre(categories: list[str]) -> str:
    text = " | ".join(categories).casefold()
    if not text:
        return ""
    for code, words in GENRE_KEYWORDS:
        if any(w in text for w in words):
            return code
    return ""


def map_language(codes: list[str]) -> str:
    for code in codes:
        if mapped := LANGUAGE_CODES.get((code or "").lower()):
            return mapped
    return "other" if codes else ""


def normalize_isbn(text: str) -> str:
    """'978-966-2355-57-4' -> '9789662355574'; returns "" if it is not an ISBN-10/13."""
    raw = _ISBN_CHARS.sub("", text or "").upper()
    if re.fullmatch(r"\d{13}", raw) or re.fullmatch(r"\d{9}[\dX]", raw):
        return raw
    return ""


def year_of(date: str | int | None) -> str:
    m = re.search(r"\d{4}", str(date or ""))
    return m.group(0) if m else ""
