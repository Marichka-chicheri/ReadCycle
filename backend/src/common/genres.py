"""Fixed list of book genres: code -> Ukrainian label.

Codes are stored in DynamoDB, labels are shown in the UI. The frontend keeps the same list in
frontend/src/genres.js; change both together. Never rename an existing code (stored data uses it).
"""

GENRES: dict[str, str] = {
    "classic": "Класика",
    "modern": "Сучасна проза",
    "fantasy": "Фентезі",
    "scifi": "Наукова фантастика",
    "detective": "Детектив",
    "thriller": "Трилер",
    "horror": "Жахи",
    "romance": "Любовний роман",
    "historical": "Історичний роман",
    "young_adult": "Young Adult",
    "poetry": "Поезія",
    "drama": "Драматургія",
    "children": "Дитяча",
    "comics": "Комікси і графічні романи",
    "nonfiction": "Нон-фікшн",
    "biography": "Біографії та мемуари",
    "history": "Історія",
    "philosophy": "Філософія",
    "psychology": "Психологія",
    "science": "Наука і техніка",
    "business": "Бізнес і саморозвиток",
    "religion": "Релігія і духовність",
    "textbook": "Навчальна література",
    "other": "Інше",
}


def is_genre(code: str) -> bool:
    return code in GENRES
