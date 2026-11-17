"""Bans, blocks and complaints. Key layout (all in the main table):

ban:        pk=USER#<id>           sk=BAN                       (gsi1pk="BAN")
block:      pk=USER#<me>           sk=BLOCK#<other>             I blocked them
            pk=USER#<other>        sk=BLOCKEDBY#<me>            mirror: hiding works both ways
complaint:  pk=REPORT#<type>#<id>  sk=BY#<reporter>             the complaint (gsi1pk="REPORT")
            pk=USER#<reporter>     sk=REPORTSENT#<iso>#<target> for the daily limit
            pk=USER#<owner>        sk=COMPLAINT#<reporter>      distinct complainants per account
"""

from datetime import UTC, datetime, timedelta

from common.db import CATALOG_INDEX, user_pk
from domain.ban import Ban
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

    def delete(self, user_id: str) -> None:
        self._table.delete_item(Key={"pk": user_pk(user_id), "sk": "BAN"})

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
        self._table.put_item(
            Item={
                "pk": user_pk(report.owner_id),
                "sk": f"COMPLAINT#{report.reporter_id}",
                "created_at": report.created_at,
            }
        )

    def sent_last_day(self, reporter_id: str) -> int:
        cutoff = (datetime.now(UTC) - timedelta(days=1)).isoformat(timespec="milliseconds")
        prefix = "REPORTSENT#"
        sent = _by_prefix(self._table, user_pk(reporter_id), prefix)
        return sum(1 for i in sent if i["sk"][len(prefix) :] >= cutoff)

    def complainants(self, owner_id: str) -> int:
        """How many different students have complained about this user or their books."""
        return len(_by_prefix(self._table, user_pk(owner_id), "COMPLAINT#"))

    def clear_complaints(self, owner_id: str) -> None:
        for item in _by_prefix(self._table, user_pk(owner_id), "COMPLAINT#"):
            self._table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})

    def open_reports(self) -> list[Report]:
        return [Report.from_item(i) for i in _by_index(self._table, "REPORT")]

    def for_target(self, target_type: str, target_id: str) -> list[Report]:
        items = _by_prefix(self._table, f"REPORT#{target_type}#{target_id}", "BY#")
        return [Report.from_item(i) for i in items]

    def close(self, target_type: str, target_id: str, status: str, handled_by: str) -> int:
        reports = [r for r in self.for_target(target_type, target_id) if r.status == STATUS_OPEN]
        for r in reports:
            r.status, r.handled_by = status, handled_by
            self._table.put_item(Item=r.to_item())
        return len(reports)
