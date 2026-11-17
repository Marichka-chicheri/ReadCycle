"""GET /users/{id} — another student's public profile: contacts, shelf and wishlist."""

from common.db import main_table
from common.http import ApiError, api_handler, current_user
from common.moderation import hidden_users
from repositories.books import BookRepository
from repositories.profiles import ProfileRepository
from repositories.wishes import WishRepository


def get_repos() -> tuple[ProfileRepository, BookRepository, WishRepository]:
    table = main_table()
    return ProfileRepository(table), BookRepository(table), WishRepository(table)


@api_handler
def handler(event, context):
    viewer_id, _ = current_user(event)  # any signed-in student may look
    user_id = (event.get("pathParameters") or {}).get("id", "")
    profiles, books, wishes = get_repos()
    profile = profiles.get(user_id) if user_id else None
    # banned or blocked: indistinguishable from "no such profile"
    if profile and user_id in hidden_users(viewer_id):
        profile = None
    if not profile:
        raise ApiError(404, "NOT_FOUND", "Профіль не знайдено")
    return {
        "profile": profile.to_public_json(),
        "books": [b.to_json() for b in books.list_by_owner(user_id) if not b.is_given],
        "wishes": [w.to_json() for w in wishes.list_by_owner(user_id)],
    }
