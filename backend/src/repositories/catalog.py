from common.db import CATALOG_INDEX
from domain.book import Book
from domain.wish import Wish


class CatalogRepository:
    """Reads everyone's books / wishes through the catalog index (gsi1pk = "BOOK" | "WISH")."""

    def __init__(self, table):
        self._table = table

    def _all(self, kind: str) -> list[dict]:
        items, start = [], None
        while True:
            kwargs = {
                "IndexName": CATALOG_INDEX,
                "KeyConditionExpression": "gsi1pk = :pk",
                "ExpressionAttributeValues": {":pk": kind},
                "ScanIndexForward": False,  # newest first
            }
            if start:
                kwargs["ExclusiveStartKey"] = start
            page = self._table.query(**kwargs)
            items += page.get("Items", [])
            start = page.get("LastEvaluatedKey")
            if not start:
                return items

    def all_books(self) -> list[Book]:
        return [Book.from_item(i) for i in self._all("BOOK")]

    def all_wishes(self) -> list[Wish]:
        return [Wish.from_item(i) for i in self._all("WISH")]
