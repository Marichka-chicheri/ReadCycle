"""GET /profile — the signed-in user's own profile ({"profile": null} before onboarding).
PUT /profile — create or update it (the same call is used by onboarding and by editing)."""

from common.db import main_table
from common.http import api_handler, current_user, json_body
from domain.profile import Profile
from repositories.profiles import ProfileRepository


def get_repo() -> ProfileRepository:
    return ProfileRepository(main_table())


@api_handler
def get_handler(event, context):
    user_id, _ = current_user(event)
    profile = get_repo().get(user_id)
    return {"profile": profile.to_owner_json() if profile else None}


@api_handler
def put_handler(event, context):
    user_id, email = current_user(event)
    repo = get_repo()
    profile = Profile.from_input(user_id, email, json_body(event), existing=repo.get(user_id))
    repo.save(profile)
    return {"profile": profile.to_owner_json()}
