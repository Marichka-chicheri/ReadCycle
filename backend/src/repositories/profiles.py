from common.db import user_pk
from domain.profile import Profile


class ProfileRepository:
    """Profiles are stored as pk=USER#<id>, sk=PROFILE."""

    def __init__(self, table):
        self._table = table

    def get(self, user_id: str) -> Profile | None:
        item = self._table.get_item(Key={"pk": user_pk(user_id), "sk": "PROFILE"}).get("Item")
        return Profile.from_item(item) if item else None

    def save(self, profile: Profile) -> None:
        self._table.put_item(Item=profile.to_item())
