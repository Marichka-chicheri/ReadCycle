"""User profile: who the person is and how to reach them.

A profile is created on the first sign-in (onboarding) and can be edited later.
Required: display name and at least one contact (Telegram or phone). Everything else is optional.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from common.genres import is_genre
from common.http import ValidationError

NAME_MIN, NAME_MAX = 2, 60
ABOUT_MAX = 600
AGE_MIN, AGE_MAX = 14, 99
MAX_FAVORITE_GENRES = 10

_TELEGRAM_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")
_PHONE_RE = re.compile(r"^\+\d{10,15}$")


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def normalize_telegram(value: str) -> str:
    """'@Anna_K', 't.me/Anna_K', 'https://t.me/Anna_K' -> 'Anna_K'."""
    v = (value or "").strip()
    v = re.sub(r"^(https?://)?(www\.)?t(elegram)?\.me/", "", v, flags=re.IGNORECASE)
    return v.lstrip("@").strip()


def normalize_phone(value: str) -> str:
    """'097 123 45 67', '(097)123-45-67', '380971234567' -> '+380971234567'."""
    v = re.sub(r"[\s\-()]", "", value or "")
    if not v:
        return ""
    if v.startswith("0") and len(v) == 10:  # Ukrainian local format
        v = "+38" + v
    elif v.startswith("380"):
        v = "+" + v
    return v


@dataclass
class Profile:
    user_id: str
    email: str
    display_name: str
    telegram: str = ""
    phone: str = ""
    age: int | None = None
    about: str = ""
    favorite_genres: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    # ----- construction from user input -----

    @classmethod
    def from_input(
        cls, user_id: str, email: str, data: dict[str, Any], existing: Profile | None = None
    ) -> Profile:
        """Validate and normalise the editable fields. Raises ValidationError with per-field
        messages so the form can show each one next to its input."""
        errors: dict[str, str] = {}

        name = " ".join(str(data.get("display_name") or "").split())
        if not NAME_MIN <= len(name) <= NAME_MAX:
            errors["display_name"] = f"Вкажіть ім'я або нік ({NAME_MIN}–{NAME_MAX} символів)"

        telegram = normalize_telegram(str(data.get("telegram") or ""))
        if telegram and not _TELEGRAM_RE.match(telegram):
            errors["telegram"] = "Нікнейм Telegram: 5–32 символи, латиниця, цифри і _"

        phone = normalize_phone(str(data.get("phone") or ""))
        if phone and not _PHONE_RE.match(phone):
            errors["phone"] = "Номер у форматі +380XXXXXXXXX"

        if not telegram and not phone and "telegram" not in errors and "phone" not in errors:
            errors["contacts"] = "Вкажіть хоча б один контакт: Telegram або телефон"

        age = data.get("age")
        if age in (None, ""):
            age = None
        else:
            try:
                age = int(age)
            except (TypeError, ValueError):
                age = -1
            if not AGE_MIN <= age <= AGE_MAX:
                errors["age"] = f"Вік від {AGE_MIN} до {AGE_MAX}"

        about = str(data.get("about") or "").strip()
        if len(about) > ABOUT_MAX:
            errors["about"] = f"Не більше {ABOUT_MAX} символів"

        genres_in = data.get("favorite_genres") or []
        if not isinstance(genres_in, list):
            genres_in = []
        genres = list(dict.fromkeys(g for g in genres_in if isinstance(g, str)))  # dedupe
        if any(not is_genre(g) for g in genres):
            errors["favorite_genres"] = "Невідомий жанр"
        elif len(genres) > MAX_FAVORITE_GENRES:
            errors["favorite_genres"] = f"Оберіть не більше {MAX_FAVORITE_GENRES} жанрів"

        if errors:
            raise ValidationError(errors)

        ts = now_iso()
        return cls(
            user_id=user_id,
            email=email,
            display_name=name,
            telegram=telegram,
            phone=phone,
            age=age,
            about=about,
            favorite_genres=genres,
            created_at=existing.created_at if existing else ts,
            updated_at=ts,
        )

    # ----- DynamoDB mapping -----

    def to_item(self) -> dict[str, Any]:
        item = {"pk": f"USER#{self.user_id}", "sk": "PROFILE", "type": "PROFILE", **asdict(self)}
        if self.age is None:
            del item["age"]  # DynamoDB does not need explicit nulls
        return item

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Profile:
        age = item.get("age")
        return cls(
            user_id=item["user_id"],
            email=item["email"],
            display_name=item["display_name"],
            telegram=item.get("telegram", ""),
            phone=item.get("phone", ""),
            age=int(age) if age is not None else None,  # boto3 returns numbers as Decimal
            about=item.get("about", ""),
            favorite_genres=list(item.get("favorite_genres", [])),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
        )

    # ----- API representation -----

    def to_owner_json(self) -> dict[str, Any]:
        """Everything, for the owner of the profile."""
        return asdict(self)
