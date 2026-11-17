"""POST /reports — a complaint about a book or a student.

Body: {target_type: "book"|"user", target_id, owner_id (for a book), reason, comment}.

Limits: a student can send MAX_REPORTS_PER_DAY complaints a day; when AUTO_BAN_COMPLAINANTS
different students have complained about the same account, it is suspended automatically until
a moderator reviews it. Complaints are stored in the main table (the moderator page reads them)
and written to the log.
"""

import logging

from common.db import main_table
from common.http import ApiError, api_handler, current_user, json_body
from common.moderation import assert_not_banned, ban_repo
from domain.ban import AUTO, Ban
from domain.report import AUTO_BAN_COMPLAINANTS, MAX_REPORTS_PER_DAY, TARGET_BOOK, Report
from repositories.books import BookRepository
from repositories.moderation import ReportRepository
from repositories.profiles import ProfileRepository

log = logging.getLogger(__name__)


def get_repos() -> tuple[BookRepository, ProfileRepository, ReportRepository]:
    table = main_table()
    return BookRepository(table), ProfileRepository(table), ReportRepository(table)


@api_handler
def create_handler(event, context):
    reporter_id, reporter_email = current_user(event)
    assert_not_banned(reporter_id)
    data = json_body(event)
    report = Report.from_input(reporter_id, reporter_email, data)
    books, profiles, reports = get_repos()

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
    if reports.sent_last_day(reporter_id) >= MAX_REPORTS_PER_DAY:
        raise ApiError(
            429,
            "TOO_MANY_REPORTS",
            f"Не більше {MAX_REPORTS_PER_DAY} скарг на добу. Спробуйте завтра.",
        )

    reports.save(report)
    log.warning(
        "REPORT %s %s (owner %s) by %s: %s %s",
        report.target_type,
        report.target_id,
        report.owner_id,
        reporter_id,
        report.reason,
        report.comment,
    )

    complainants = reports.complainants(report.owner_id)
    bans = ban_repo()
    if complainants >= AUTO_BAN_COMPLAINANTS and not bans.get(report.owner_id):
        bans.save(Ban.create(report.owner_id, AUTO, f"Автоматично: скарг від {complainants} осіб"))
        log.warning("AUTO-BAN %s after complaints from %s students", report.owner_id, complainants)
    return {"reported": True}
