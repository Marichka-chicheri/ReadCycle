"""Book languages: code -> Ukrainian label. Mirrored in frontend/src/genres.js (LANGUAGES)."""

LANGUAGES: dict[str, str] = {
    "uk": "Українська",
    "en": "Англійська",
    "pl": "Польська",
    "de": "Німецька",
    "fr": "Французька",
    "es": "Іспанська",
    "it": "Італійська",
    "other": "Інша",
}


def is_language(code: str) -> bool:
    return code in LANGUAGES
