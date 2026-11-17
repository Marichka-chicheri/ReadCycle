"""Who is a moderator, and who is banned.

Moderators are the emails listed in the MODERATOR_EMAILS environment variable (comma separated;
set from the MODERATOR_EMAILS GitHub variable at deploy time). Emails come from the Cognito ID
token and are verified, so the list cannot be spoofed by signing up with someone else's address.
"""

import os

from common.db import main_table
from common.http import ApiError, current_user


def moderator_emails() -> set[str]:
    raw = os.environ.get("MODERATOR_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def is_moderator(email: str) -> bool:
    return email.strip().lower() in moderator_emails()


def require_moderator(event: dict) -> tuple[str, str]:
    """(user_id, email) of the signed-in moderator, or 403."""
    user_id, email = current_user(event)
    if not is_moderator(email):
        raise ApiError(403, "FORBIDDEN", "Лише для модераторів")
    return user_id, email


def ban_repo():
    from repositories.moderation import BanRepository

    return BanRepository(main_table())


def hidden_users(viewer_id: str) -> set[str]:
    """Accounts the viewer must not see: banned, blocked by them, or who blocked them."""
    from repositories.moderation import BlockRepository

    return ban_repo().banned_ids() | BlockRepository(main_table()).hidden_for(viewer_id)


def assert_not_banned(user_id: str) -> None:
    """Banned students can still look around their own account but cannot add or change things."""
    if ban_repo().get(user_id):
        raise ApiError(403, "ACCOUNT_BANNED", "Ваш акаунт заблоковано модератором")
