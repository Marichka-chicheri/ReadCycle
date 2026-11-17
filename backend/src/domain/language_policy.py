"""No Russian-language books on ReadCycle.

Catalogues do not always say a book is in Russian, so several signals are combined:
- the language code from the catalogue ("ru" / "rus");
- the ISBN: group 5 (978-5…, ISBN-10 5…) is the Russian publishing group, while Ukrainian books
  are 978-966 / 978-617;
- the letters: ы, э, ъ, ё exist in Russian but not in Ukrainian, and a Russian title often has the
  conjunction "и" or words like "что", "это". Text with і, ї, є, ґ (Ukrainian) or ў (Belarusian)
  is never treated as Russian, so "Майстер і Маргарита" or a Belarusian book stays (same for
  Serbian / Macedonian letters).

It is a heuristic: a short Russian title without any of these signs ("Идиот") cannot be told
apart from Ukrainian by letters alone. Such books are left to complaints and the moderator.
"""

from __future__ import annotations

import re

RUSSIAN_CODES = {"ru", "rus"}
REJECT_MESSAGE = "Книги російською мовою на ReadCycle не додаються"

_NOT_RUSSIAN = set("іїєґўђћџљњјѓќѕ")  # Ukrainian, Belarusian; Serbian / Macedonian
_ONLY_RUSSIAN = set("ыэъё")
# Short everyday Russian words that do not exist in Ukrainian (Ukrainian: і, що, це, як, або …).
_RUSSIAN_WORDS = {
    "и", "что", "чтобы", "это", "как", "его", "она", "они", "или", "из", "под", "нет", "есть",
    "был", "была", "было", "были", "только", "очень", "почти", "когда", "кто", "где", "мне",
    "меня", "него", "хорошая", "хороший", "хорошее", "новая", "новое", "состояние",
}  # fmt: skip
_WORD = re.compile(r"[а-яёіїєґўʼ'’]+")


def is_russian_text(*texts: str) -> bool:
    text = " ".join(t for t in texts if t).casefold()
    if not text or _NOT_RUSSIAN & set(text):
        return False
    if _ONLY_RUSSIAN & set(text):
        return True
    return any(word in _RUSSIAN_WORDS for word in _WORD.findall(text))


def is_russian_isbn(isbn: str) -> bool:
    """`isbn`: digits only (see book_metadata.normalize_isbn)."""
    return isbn.startswith("9785") if len(isbn) == 13 else len(isbn) == 10 and isbn[0] == "5"


def is_russian_language(codes: list[str]) -> bool:
    """True when the catalogue lists only Russian. A work with editions in several languages
    (Open Library lists all of them) is judged by its title and ISBN instead."""
    codes = [c.lower() for c in codes if c]
    return bool(codes) and all(c in RUSSIAN_CODES for c in codes)


def russian_fields(**texts: str) -> dict[str, str]:
    """Validation errors for form fields written in Russian (each field is judged on its own)."""
    return {name: REJECT_MESSAGE for name, text in texts.items() if is_russian_text(text)}


def is_russian_book(
    title: str = "", author: str = "", isbn: str = "", languages: list[str] | None = None
) -> bool:
    return (
        is_russian_language(languages or [])
        or (bool(isbn) and is_russian_isbn(isbn))
        or is_russian_text(title, author)
    )
