"""GET /profile — the signed-in user's own profile ({"profile": null} before onboarding).
PUT /profile — create or update it (the same call is used by onboarding and by editing).
DELETE /profile — delete the account's data: profile, books, wishlist, blocks, photos.
                  The browser then deletes the Cognito sign-in with the user's own session."""

from common.crud import forget_photos
from common.db import main_table
from common.http import api_handler, current_user, json_body
from common.moderation import assert_not_banned, ban_repo, is_moderator
from domain.profile import Profile
from repositories.account import AccountRepository
from repositories.profiles import ProfileRepository


def get_repo() -> ProfileRepository:
    return ProfileRepository(main_table())


@api_handler
def get_handler(event, context):
    user_id, email = current_user(event)
    profile = get_repo().get(user_id)
    return {
        "profile": profile.to_owner_json() if profile else None,
        "moderator": is_moderator(email),
        "banned": ban_repo().get(user_id) is not None,
    }


@api_handler
def put_handler(event, context):
    user_id, email = current_user(event)
    assert_not_banned(user_id)
    repo = get_repo()
    existing = repo.get(user_id)
    profile = Profile.from_input(user_id, email, json_body(event), existing=existing)
    repo.save(profile)
    if existing:
        forget_photos(existing.photo_keys() - profile.photo_keys())  # a replaced photo
    return {"profile": profile.to_owner_json()}


def get_account_repo() -> AccountRepository:
    return AccountRepository(main_table())


@api_handler
def delete_handler(event, context):
    user_id, _ = current_user(event)
    # a banned student must not escape the ban by deleting and signing up again
    assert_not_banned(user_id)
    forget_photos(get_account_repo().delete(user_id))
    return {"deleted": True}
