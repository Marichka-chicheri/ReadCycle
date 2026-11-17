"""Blocking: "I do not want to see this student" (and they do not see me).

GET    /my/blocks      — the students I blocked, with names
PUT    /blocks/{id}    — block a student
DELETE /blocks/{id}    — unblock

Blocked students vanish from each other's catalog, matches and profile pages.
"""

from common.db import main_table
from common.http import ApiError, api_handler, current_user
from repositories.moderation import BlockRepository
from repositories.profiles import ProfileRepository


def get_repos() -> tuple[BlockRepository, ProfileRepository]:
    table = main_table()
    return BlockRepository(table), ProfileRepository(table)


def _target(event, me: str) -> str:
    other = (event.get("pathParameters") or {}).get("id", "")
    if not other:
        raise ApiError(400, "BAD_REQUEST", "Id is required")
    if other == me:
        raise ApiError(400, "OWN_ITEM", "Не можна заблокувати себе")
    return other


@api_handler
def list_handler(event, context):
    me, _ = current_user(event)
    blocks, profiles = get_repos()
    result = []
    for user_id in blocks.blocked_by_me(me):
        profile = profiles.get(user_id)
        result.append(
            {"user_id": user_id, "display_name": profile.display_name if profile else "Студент УКУ"}
        )
    return {"blocks": result}


@api_handler
def block_handler(event, context):
    me, _ = current_user(event)
    other = _target(event, me)
    blocks, profiles = get_repos()
    if not profiles.get(other):
        raise ApiError(404, "NOT_FOUND", "Профіль не знайдено")
    blocks.block(me, other)
    return {"blocked": other}


@api_handler
def unblock_handler(event, context):
    me, _ = current_user(event)
    other = _target(event, me)
    get_repos()[0].unblock(me, other)
    return {"unblocked": other}
