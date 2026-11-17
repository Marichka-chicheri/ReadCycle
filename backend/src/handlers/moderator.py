"""Moderator API (only for emails in MODERATOR_EMAILS).

GET    /mod/reports          — open complaints grouped by target, most complained first
POST   /mod/reports/resolve  — {target_type, target_id, action: dismiss | remove_book | ban_user}
                             dismiss and ban_user close ALL open complaints about that student;
                             remove_book closes only the complaints about that book
GET    /mod/bans             — suspended accounts
POST   /mod/bans/{id}        — suspend an account  {reason}
DELETE /mod/bans/{id}        — lift a suspension
"""

from collections import defaultdict

from common.crud import forget_photos
from common.db import main_table
from common.http import ApiError, api_handler, json_body
from common.moderation import require_moderator
from domain.ban import Ban
from domain.report import STATUS_ACTED, STATUS_DISMISSED, TARGET_BOOK, TARGETS
from repositories.books import BookRepository
from repositories.moderation import BanRepository, ReportRepository
from repositories.profiles import ProfileRepository

ACTIONS = ("dismiss", "remove_book", "ban_user")


def get_repos() -> tuple[ReportRepository, BanRepository, BookRepository, ProfileRepository]:
    table = main_table()
    return (
        ReportRepository(table),
        BanRepository(table),
        BookRepository(table),
        ProfileRepository(table),
    )


def _name(profiles: ProfileRepository, user_id: str) -> str:
    profile = profiles.get(user_id)
    return profile.display_name if profile else "Студент УКУ"


@api_handler
def reports_handler(event, context):
    require_moderator(event)
    reports, bans, books, profiles = get_repos()
    banned = bans.banned_ids()

    groups = defaultdict(list)
    for r in reports.open_reports():
        groups[(r.target_type, r.target_id)].append(r)

    result = []
    for (target_type, target_id), items in groups.items():
        first = items[0]
        owner_id = first.owner_id
        book = books.get(owner_id, target_id) if target_type == TARGET_BOOK else None
        result.append(
            {
                "target_type": target_type,
                "target_id": target_id,
                "owner_id": owner_id,
                "owner_name": _name(profiles, owner_id),
                "title": first.title,
                "book_exists": bool(book) if target_type == TARGET_BOOK else None,
                "owner_banned": owner_id in banned,
                "count": len(items),
                "last_at": max(r.created_at for r in items),
                "reports": [
                    {"reason": r.reason, "comment": r.comment, "created_at": r.created_at}
                    for r in items
                ],
            }
        )
    result.sort(key=lambda g: (-g["count"], g["last_at"]))
    return {"groups": result}


@api_handler
def resolve_handler(event, context):
    _, email = require_moderator(event)
    data = json_body(event)
    target_type = str(data.get("target_type") or "")
    target_id = str(data.get("target_id") or "")
    action = str(data.get("action") or "")
    if target_type not in TARGETS or not target_id or action not in ACTIONS:
        raise ApiError(400, "BAD_REQUEST", "Невірні параметри")

    reports, bans, books, _ = get_repos()
    group = reports.for_target(target_type, target_id)
    if not group:
        raise ApiError(404, "NOT_FOUND", "Скарги не знайдено")
    owner_id = group[0].owner_id

    if action == "dismiss":  # nothing wrong with this student: all claims against them go away
        reports.close_for_owner(owner_id, STATUS_DISMISSED, email)
        return {"resolved": "dismissed"}

    if action == "remove_book":
        if target_type != TARGET_BOOK:
            raise ApiError(400, "BAD_REQUEST", "Видалити можна лише книгу")
        book = books.get(owner_id, target_id)
        if book:
            books.delete(owner_id, target_id)
            forget_photos(book.photo_keys())
        reports.close(target_type, target_id, STATUS_ACTED, email)
    else:  # ban_user: the decision covers everything reported about this student
        if not bans.get(owner_id):
            bans.save(Ban.create(owner_id, email, "Рішення модератора"))
        reports.close_for_owner(owner_id, STATUS_ACTED, email)
    return {"resolved": "acted"}


@api_handler
def bans_handler(event, context):
    require_moderator(event)
    _, bans, _, profiles = get_repos()
    return {
        "bans": [
            {
                **b.__dict__,
                "display_name": _name(profiles, b.user_id),
            }
            for b in bans.all()
        ]
    }


def _user_id(event) -> str:
    user_id = (event.get("pathParameters") or {}).get("id", "")
    if not user_id:
        raise ApiError(400, "BAD_REQUEST", "Id is required")
    return user_id


@api_handler
def ban_handler(event, context):
    me, email = require_moderator(event)
    user_id = _user_id(event)
    if user_id == me:
        raise ApiError(400, "OWN_ITEM", "Не можна заблокувати себе")
    _, bans, _, profiles = get_repos()
    if not profiles.get(user_id):
        raise ApiError(404, "NOT_FOUND", "Профіль не знайдено")
    reason = str(json_body(event).get("reason") or "")
    bans.save(Ban.create(user_id, email, reason or "Рішення модератора"))
    return {"banned": user_id}


@api_handler
def unban_handler(event, context):
    require_moderator(event)
    user_id = _user_id(event)
    get_repos()[1].delete(user_id)
    return {"unbanned": user_id}
