from domain.book import Book
from repositories.base import OwnedItemRepository

MAX_BOOKS_PER_USER = 200


class BookRepository(OwnedItemRepository[Book]):
    """A user's books: pk=USER#<owner>, sk=BOOK#<id>."""

    prefix = "BOOK"
    entity = Book
