"""Generic repository for items that belong to one user: pk=USER#<owner>, sk=<PREFIX>#<id>.

Subclasses only say which entity class they store and under which sort-key prefix
(see BookRepository, WishRepository). The entity must provide `id`, `owner_id`, `created_at`,
`to_item()` and `from_item()`.
"""

from typing import ClassVar

from common.db import user_pk


class OwnedItemRepository[T]:
    prefix: ClassVar[str]  # e.g. "BOOK"
    entity: ClassVar[type]  # e.g. Book

    def __init__(self, table):
        self._table = table

    def _key(self, owner_id: str, item_id: str) -> dict:
        return {"pk": user_pk(owner_id), "sk": f"{self.prefix}#{item_id}"}

    def list_by_owner(self, owner_id: str) -> list[T]:
        items, start = [], None
        while True:
            kwargs = {
                "KeyConditionExpression": "pk = :pk AND begins_with(sk, :prefix)",
                "ExpressionAttributeValues": {
                    ":pk": user_pk(owner_id),
                    ":prefix": f"{self.prefix}#",
                },
            }
            if start:
                kwargs["ExclusiveStartKey"] = start
            page = self._table.query(**kwargs)
            items += page.get("Items", [])
            start = page.get("LastEvaluatedKey")
            if not start:
                break
        entities = [self.entity.from_item(i) for i in items]
        return sorted(entities, key=lambda e: e.created_at)

    def get(self, owner_id: str, item_id: str) -> T | None:
        item = self._table.get_item(Key=self._key(owner_id, item_id)).get("Item")
        return self.entity.from_item(item) if item else None

    def count(self, owner_id: str) -> int:
        return len(self.list_by_owner(owner_id))

    def save(self, entity: T) -> None:
        self._table.put_item(Item=entity.to_item())

    def delete(self, owner_id: str, item_id: str) -> None:
        self._table.delete_item(Key=self._key(owner_id, item_id))
