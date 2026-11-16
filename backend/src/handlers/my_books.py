"""The signed-in user's own books (their shelf in the profile).

GET    /my/books        — list
POST   /my/books        — add a book
PUT    /my/books/{id}   — edit a book
DELETE /my/books/{id}   — remove a book
"""

from common.db import main_table
from common.http import ApiError, api_handler, current_user, json_body
from domain.book import Book
from repositories.books import MAX_BOOKS_PER_USER, BookRepository


def get_repo() -> BookRepository:
    return BookRepository(main_table())


def _book_id(event) -> str:
    book_id = (event.get("pathParameters") or {}).get("id", "")
    if not book_id:
        raise ApiError(400, "BAD_REQUEST", "Book id is required")
    return book_id


def _own_book(repo: BookRepository, owner_id: str, book_id: str) -> Book:
    book = repo.get(owner_id, book_id)
    if not book:
        raise ApiError(404, "NOT_FOUND", "Книгу не знайдено")
    return book


@api_handler
def list_handler(event, context):
    owner_id, _ = current_user(event)
    return {"books": [b.to_json() for b in get_repo().list_by_owner(owner_id)]}


@api_handler
def create_handler(event, context):
    owner_id, _ = current_user(event)
    repo = get_repo()
    book = Book.from_input(owner_id, json_body(event))
    if repo.count(owner_id) >= MAX_BOOKS_PER_USER:
        raise ApiError(400, "LIMIT_REACHED", f"Не більше {MAX_BOOKS_PER_USER} книг на полиці")
    repo.save(book)
    return {"book": book.to_json()}


@api_handler
def update_handler(event, context):
    owner_id, _ = current_user(event)
    repo = get_repo()
    existing = _own_book(repo, owner_id, _book_id(event))
    book = Book.from_input(owner_id, json_body(event), existing=existing)
    repo.save(book)
    return {"book": book.to_json()}


@api_handler
def delete_handler(event, context):
    owner_id, _ = current_user(event)
    repo = get_repo()
    book = _own_book(repo, owner_id, _book_id(event))
    repo.delete(owner_id, book.book_id)
    return {"deleted": book.book_id}
