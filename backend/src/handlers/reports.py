"""POST /reports — a complaint about a book or a student.

Body: {target_type: "book"|"user", target_id, owner_id (for a book), reason, comment}.
Complaints are stored in the main table and written to the log; a moderator reads them there.
"""

import logging

from common.db import main_table
from common.http import ApiError, api_handler, current_user, json_body
from domain.report import TARGET_BOOK, Report
from repositories.books import BookRepository
from repositories.profiles import ProfileRepository

log = logging.getLogger(__name__)


def get_repos() -> tuple[BookRepository, ProfileRepository]:
    table = main_table()
    return BookRepository(table), ProfileRepository(table)


def get_table():
    return main_table()


@api_handler
def create_handler(event, context):
    reporter_id, reporter_email = current_user(event)
    data = json_body(event)
    report = Report.from_input(reporter_id, reporter_email, data)
    books, profiles = get_repos()

    if report.target_type == TARGET_BOOK:
        owner_id = str(data.get("owner_id") or "")
        book = books.get(owner_id, report.target_id) if owner_id else None
        if not book:
            raise ApiError(404, "NOT_FOUND", "Книгу не знайдено")
        report.owner_id, report.title = book.owner_id, book.title
    else:
        if not profiles.get(report.target_id):
            raise ApiError(404, "NOT_FOUND", "Профіль не знайдено")
        report.owner_id = report.target_id

    if report.owner_id == reporter_id:
        raise ApiError(400, "OWN_ITEM", "Не можна поскаржитись на себе")

    get_table().put_item(Item=report.to_item())
    log.warning(
        "REPORT %s %s (owner %s) by %s: %s %s",
        report.target_type,
        report.target_id,
        report.owner_id,
        reporter_id,
        report.reason,
        report.comment,
    )
    return {"reported": True}
