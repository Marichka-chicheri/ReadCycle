from common.db import user_pk
from domain.book import Book

MAX_BOOKS_PER_USER = 200


class BookRepository:
    """A user's books: pk=USER#<owner>, sk=BOOK#<id>."""

    def __init__(self, table):
        self._table = table

    def list_by_owner(self, owner_id: str) -> list[Book]:
        items, start = [], None
        while True:
            kwargs = {
                "KeyConditionExpression": "pk = :pk AND begins_with(sk, :prefix)",
                "ExpressionAttributeValues": {":pk": user_pk(owner_id), ":prefix": "BOOK#"},
            }
            if start:
                kwargs["ExclusiveStartKey"] = start
            page = self._table.query(**kwargs)
            items += page.get("Items", [])
            start = page.get("LastEvaluatedKey")
            if not start:
                break
        books = [Book.from_item(i) for i in items]
        return sorted(books, key=lambda b: b.created_at)

    def get(self, owner_id: str, book_id: str) -> Book | None:
        key = {"pk": user_pk(owner_id), "sk": f"BOOK#{book_id}"}
        item = self._table.get_item(Key=key).get("Item")
        return Book.from_item(item) if item else None

    def count(self, owner_id: str) -> int:
        return len(self.list_by_owner(owner_id))

    def save(self, book: Book) -> None:
        self._table.put_item(Item=book.to_item())

    def delete(self, owner_id: str, book_id: str) -> None:
        self._table.delete_item(Key={"pk": user_pk(owner_id), "sk": f"BOOK#{book_id}"})
