"""The signed-in user's own books (their shelf in the profile).

GET    /my/books        — list
POST   /my/books        — add a book
PUT    /my/books/{id}   — edit a book
DELETE /my/books/{id}   — remove a book
"""

from common.crud import OwnedCollectionApi
from common.db import main_table
from common.http import api_handler
from domain.book import Book
from repositories.books import MAX_BOOKS_PER_USER, BookRepository


def get_repo() -> BookRepository:
    return BookRepository(main_table())


collection = OwnedCollectionApi(
    repo_factory=lambda: get_repo(),  # looked up at call time, so tests can replace get_repo
    entity=Book,
    name="book",
    plural="books",
    limit=MAX_BOOKS_PER_USER,
    not_found="Книгу не знайдено",
    limit_message=f"Не більше {MAX_BOOKS_PER_USER} книг на полиці",
)

list_handler = api_handler(collection.list)
create_handler = api_handler(collection.create)
update_handler = api_handler(collection.update)
delete_handler = api_handler(collection.delete)
