"""Bans, blocks and complaints. Key layout (all in the main table):

ban:        pk=USER#<id>           sk=BAN                       (gsi1pk="BAN")
            pk=BANNED_EMAIL#<email> sk=BAN                      no new sign-up with this email
block:      pk=USER#<me>           sk=BLOCK#<other>             I blocked them
            pk=USER#<other>        sk=BLOCKEDBY#<me>            mirror: hiding works both ways
complaint:  pk=REPORT#<type>#<id>  sk=BY#<reporter>             the complaint (gsi1pk="REPORT")
            pk=USER#<reporter>     sk=REPORTSENT#<iso>#<target> for the daily limit
"""

from datetime import UTC, datetime, timedelta

from common.db import CATALOG_INDEX, user_pk
from domain.ban import Ban, banned_email_pk, normalize_email
from domain.profile import now_iso
from domain.report import STATUS_OPEN, Report


def _by_prefix(table, pk: str, prefix: str) -> list[dict]:
    items, start = [], None
    while True:
        kwargs = {
            "KeyConditionExpression": "pk = :pk AND begins_with(sk, :prefix)",
            "ExpressionAttributeValues": {":pk": pk, ":prefix": prefix},
        }
        if start:
            kwargs["ExclusiveStartKey"] = start
        page = table.query(**kwargs)
        items += page.get("Items", [])
        start = page.get("LastEvaluatedKey")
        if not start:
            return items


def _by_index(table, kind: str) -> list[dict]:
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
        page = table.query(**kwargs)
        items += page.get("Items", [])
        start = page.get("LastEvaluatedKey")
        if not start:
            return items


class BanRepository:
    def __init__(self, table):
        self._table = table

    def get(self, user_id: str) -> Ban | None:
        item = self._table.get_item(Key={"pk": user_pk(user_id), "sk": "BAN"}).get("Item")
        return Ban.from_item(item) if item else None

    def save(self, ban: Ban) -> None:
        self._table.put_item(Item=ban.to_item())
        if email_item := ban.email_item():
            self._table.put_item(Item=email_item)

    def delete(self, user_id: str) -> None:
        ban = self.get(user_id)
        if ban and ban.email:
            self._table.delete_item(Key={"pk": banned_email_pk(ban.email), "sk": "BAN"})
        self._table.delete_item(Key={"pk": user_pk(user_id), "sk": "BAN"})

    def is_email_banned(self, email: str) -> bool:
        if not normalize_email(email):
            return False
        key = {"pk": banned_email_pk(email), "sk": "BAN"}
        return "Item" in self._table.get_item(Key=key)

    def all(self) -> list[Ban]:
        return [Ban.from_item(i) for i in _by_index(self._table, "BAN")]

    def banned_ids(self) -> set[str]:
        return {b.user_id for b in self.all()}


class BlockRepository:
    """ "I do not want to see this student" — hides both of them from each other."""

    def __init__(self, table):
        self._table = table

    def block(self, me: str, other: str) -> None:
        ts = now_iso()
        self._table.put_item(
            Item={"pk": user_pk(me), "sk": f"BLOCK#{other}", "blocked_id": other, "created_at": ts}
        )
        self._table.put_item(
            Item={"pk": user_pk(other), "sk": f"BLOCKEDBY#{me}", "blocker_id": me, "created_at": ts}
        )

    def unblock(self, me: str, other: str) -> None:
        self._table.delete_item(Key={"pk": user_pk(me), "sk": f"BLOCK#{other}"})
        self._table.delete_item(Key={"pk": user_pk(other), "sk": f"BLOCKEDBY#{me}"})

    def blocked_by_me(self, me: str) -> list[str]:
        return [i["blocked_id"] for i in _by_prefix(self._table, user_pk(me), "BLOCK#")]

    def hidden_for(self, me: str) -> set[str]:
        """Everyone `me` must not see: people they blocked and people who blocked them."""
        mirror = _by_prefix(self._table, user_pk(me), "BLOCKEDBY#")
        return set(self.blocked_by_me(me)) | {i["blocker_id"] for i in mirror}


class ReportRepository:
    def __init__(self, table):
        self._table = table

    def save(self, report: Report) -> None:
        self._table.put_item(Item=report.to_item())
        self._table.put_item(
            Item={
                "pk": user_pk(report.reporter_id),
                "sk": f"REPORTSENT#{report.created_at}#{report.target_type}#{report.target_id}",
            }
        )

    def sent_last_day(self, reporter_id: str) -> int:
        cutoff = (datetime.now(UTC) - timedelta(days=1)).isoformat(timespec="milliseconds")
        prefix = "REPORTSENT#"
        sent = _by_prefix(self._table, user_pk(reporter_id), prefix)
        return sum(1 for i in sent if i["sk"][len(prefix) :] >= cutoff)

    def open_reports(self) -> list[Report]:
        return [Report.from_item(i) for i in _by_index(self._table, "REPORT")]

    def for_target(self, target_type: str, target_id: str) -> list[Report]:
        items = _by_prefix(self._table, f"REPORT#{target_type}#{target_id}", "BY#")
        return [Report.from_item(i) for i in items]

    def _close_all(self, reports: list[Report], status: str, handled_by: str) -> int:
        for r in reports:
            r.status, r.handled_by = status, handled_by
            self._table.put_item(Item=r.to_item())  # moves it to REPORT_DONE: kept as history
        return len(reports)

    def close(self, target_type: str, target_id: str, status: str, handled_by: str) -> int:
        """Close the open complaints about one book or one user."""
        reports = [r for r in self.for_target(target_type, target_id) if r.status == STATUS_OPEN]
        return self._close_all(reports, status, handled_by)

    def close_for_owner(self, owner_id: str, status: str, handled_by: str) -> int:
        """Close every open complaint about this student: about them and about their books."""
        reports = [r for r in self.open_reports() if r.owner_id == owner_id]
        return self._close_all(reports, status, handled_by)
