"""CRUD API over a user's own collection (books, wishes): list / create / update / delete.

The owner always comes from the token, never from the request, so a user can only ever touch
items under their own USER#<id> partition: someone else's id simply returns 404.
"""

from collections.abc import Callable
from typing import Any

from common.http import ApiError, current_user, json_body


class OwnedCollectionApi:
    def __init__(
        self,
        repo_factory: Callable[[], Any],
        entity: type,
        name: str,
        plural: str,
        limit: int,
        not_found: str,
        limit_message: str,
    ):
        self.repo_factory = repo_factory
        self.entity = entity
        self.name = name  # one item: {"book": {...}}
        self.plural = plural  # list: {"books": [...]}
        self.limit = limit
        self.not_found = not_found
        self.limit_message = limit_message

    @staticmethod
    def _item_id(event) -> str:
        item_id = (event.get("pathParameters") or {}).get("id", "")
        if not item_id:
            raise ApiError(400, "BAD_REQUEST", "Id is required")
        return item_id

    def _own(self, repo, owner_id: str, item_id: str):
        entity = repo.get(owner_id, item_id)
        if not entity:
            raise ApiError(404, "NOT_FOUND", self.not_found)
        return entity

    def list(self, event, context):
        owner_id, _ = current_user(event)
        items = self.repo_factory().list_by_owner(owner_id)
        return {self.plural: [e.to_json() for e in items]}

    def create(self, event, context):
        owner_id, _ = current_user(event)
        repo = self.repo_factory()
        entity = self.entity.from_input(owner_id, json_body(event))
        if repo.count(owner_id) >= self.limit:
            raise ApiError(400, "LIMIT_REACHED", self.limit_message)
        repo.save(entity)
        return {self.name: entity.to_json()}

    def update(self, event, context):
        owner_id, _ = current_user(event)
        repo = self.repo_factory()
        existing = self._own(repo, owner_id, self._item_id(event))
        entity = self.entity.from_input(owner_id, json_body(event), existing=existing)
        repo.save(entity)
        return {self.name: entity.to_json()}

    def delete(self, event, context):
        owner_id, _ = current_user(event)
        repo = self.repo_factory()
        entity = self._own(repo, owner_id, self._item_id(event))
        repo.delete(owner_id, entity.id)
        return {"deleted": entity.id}
