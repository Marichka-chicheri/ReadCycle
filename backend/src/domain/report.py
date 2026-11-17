"""A complaint about a book or a user.

Stored as pk=REPORT#<target_type>#<target_id>, sk=BY#<reporter>: one complaint per person per
target (sending it again just replaces the earlier one). While open it carries gsi1pk="REPORT",
so the moderator page lists open complaints, newest first, through the catalog index (which
only reads "BOOK" / "WISH" / "BAN", so complaints never leak into it). A handled complaint
moves to gsi1pk="REPORT_DONE" and stays as history.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from common.http import ValidationError
from domain.profile import now_iso

TARGET_BOOK = "book"
TARGET_USER = "user"
TARGETS = (TARGET_BOOK, TARGET_USER)

REASONS = ("spam", "inappropriate", "scam", "other")
COMMENT_MAX = 500

STATUS_OPEN = "open"
STATUS_DISMISSED = "dismissed"  # moderator: nothing wrong
STATUS_ACTED = "acted"  # moderator: book removed / account banned

# Limit against abuse of the complaint form itself: one student cannot flood moderators.
# Complaints never block anyone by themselves: only a moderator decides.
MAX_REPORTS_PER_DAY = 5


@dataclass
class Report:
    target_type: str
    target_id: str  # book_id or user id
    reporter_id: str
    reason: str
    reporter_email: str = ""
    owner_id: str = ""  # whose book / who is reported (== target_id for a user)
    title: str = ""  # book title at the time of the complaint (a book may be deleted later)
    comment: str = ""
    status: str = STATUS_OPEN
    handled_by: str = ""
    created_at: str = ""

    @classmethod
    def from_input(cls, reporter_id: str, reporter_email: str, data: dict[str, Any]) -> Report:
        errors: dict[str, str] = {}

        target_type = str(data.get("target_type") or "")
        if target_type not in TARGETS:
            errors["target_type"] = "Невідомий об'єкт скарги"

        target_id = str(data.get("target_id") or "").strip()
        if not target_id:
            errors["target_id"] = "Вкажіть, на що скарга"

        reason = str(data.get("reason") or "")
        if reason not in REASONS:
            errors["reason"] = "Оберіть причину"

        comment = str(data.get("comment") or "").strip()
        if len(comment) > COMMENT_MAX:
            errors["comment"] = f"Не більше {COMMENT_MAX} символів"
        if reason == "other" and not comment:
            errors["comment"] = "Опишіть, що не так"

        if errors:
            raise ValidationError(errors)

        return cls(
            target_type=target_type,
            target_id=target_id,
            reporter_id=reporter_id,
            reporter_email=reporter_email,
            reason=reason,
            comment=comment,
            created_at=now_iso(),
        )

    def to_item(self) -> dict[str, Any]:
        return {
            "pk": f"REPORT#{self.target_type}#{self.target_id}",
            "sk": f"BY#{self.reporter_id}",
            "type": "REPORT",
            "gsi1pk": "REPORT" if self.status == STATUS_OPEN else "REPORT_DONE",
            "gsi1sk": f"{self.created_at}#{self.target_type}#{self.target_id}#{self.reporter_id}",
            **asdict(self),
        }

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Report:
        return cls(**{f: item.get(f, "") for f in cls.__dataclass_fields__})
