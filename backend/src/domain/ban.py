"""A suspended account.

Stored as pk=USER#<id>, sk=BAN, gsi1pk="BAN" (so every ban can be listed through the catalog
index). A banned student's books and profile disappear for everyone else and they cannot add
or change anything. Only a moderator sets or lifts a ban; complaints alone never do.

The banned email is remembered too (pk=BANNED_EMAIL#<email>, sk=BAN): deleting the account and
signing up again with the same address is refused by the Cognito pre sign-up trigger.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.profile import now_iso


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def banned_email_pk(email: str) -> str:
    return f"BANNED_EMAIL#{normalize_email(email)}"


@dataclass
class Ban:
    user_id: str
    reason: str = ""
    banned_by: str = ""  # moderator's email
    created_at: str = ""
    email: str = ""  # the banned student's own email (lower case), "" for older bans

    @classmethod
    def create(cls, user_id: str, banned_by: str, reason: str = "", email: str = "") -> Ban:
        return cls(
            user_id=user_id,
            reason=reason.strip()[:300],
            banned_by=banned_by,
            created_at=now_iso(),
            email=normalize_email(email),
        )

    def to_item(self) -> dict[str, Any]:
        return {
            "pk": f"USER#{self.user_id}",
            "sk": "BAN",
            "type": "BAN",
            "gsi1pk": "BAN",
            "gsi1sk": f"{self.created_at}#{self.user_id}",
            **asdict(self),
        }

    def email_item(self) -> dict[str, Any] | None:
        if not self.email:
            return None
        return {"pk": banned_email_pk(self.email), "sk": "BAN", "user_id": self.user_id}

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Ban:
        return cls(**{f: item.get(f, "") for f in cls.__dataclass_fields__})
