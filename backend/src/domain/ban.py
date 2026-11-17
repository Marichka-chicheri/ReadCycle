"""A suspended account.

Stored as pk=USER#<id>, sk=BAN, gsi1pk="BAN" (so every ban can be listed through the catalog
index). A banned student's books and profile disappear for everyone else and they cannot add
or change anything. Bans are set by a moderator, or automatically when enough different
students complain (the moderator then reviews it and can lift it).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.profile import now_iso

AUTO = "auto"  # banned_by value for automatic bans


@dataclass
class Ban:
    user_id: str
    reason: str = ""
    banned_by: str = ""  # moderator's email, or AUTO
    created_at: str = ""

    @classmethod
    def create(cls, user_id: str, banned_by: str, reason: str = "") -> Ban:
        return cls(
            user_id=user_id, reason=reason.strip()[:300], banned_by=banned_by, created_at=now_iso()
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

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Ban:
        return cls(**{f: item.get(f, "") for f in cls.__dataclass_fields__})
