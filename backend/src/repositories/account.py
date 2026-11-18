"""Deleting a student's account: everything stored under their USER#<id> partition, plus the
mirror items that live in other students' partitions (blocks) and their open complaints.

Photos (avatar, uploaded covers) are returned so the caller can remove them from S3. The Cognito
sign-in itself is deleted by the browser right after this (it holds the user's own session).
"""

from common.db import user_pk
from domain.book import Book
from domain.profile import Profile
from domain.report import STATUS_DISMISSED
from repositories.moderation import ReportRepository

DELETED_BY = "account deleted"


class AccountRepository:
    def __init__(self, table):
        self._table = table

    def _partition(self, user_id: str) -> list[dict]:
        items, start = [], None
        while True:
            kwargs = {
                "KeyConditionExpression": "pk = :pk",
                "ExpressionAttributeValues": {":pk": user_pk(user_id)},
            }
            if start:
                kwargs["ExclusiveStartKey"] = start
            page = self._table.query(**kwargs)
            items += page.get("Items", [])
            start = page.get("LastEvaluatedKey")
            if not start:
                return items

    def delete(self, user_id: str) -> set[str]:
        """Remove the account's data. Returns the S3 keys of its photos."""
        photos: set[str] = set()
        for item in self._partition(user_id):
            sk = item["sk"]
            if sk == "PROFILE":
                photos |= Profile.from_item(item).photo_keys()
            elif sk.startswith("BOOK#"):
                photos |= Book.from_item(item).photo_keys()
            elif sk.startswith("BLOCK#"):  # the other side's "blocked by" mirror
                other = sk.removeprefix("BLOCK#")
                self._table.delete_item(Key={"pk": user_pk(other), "sk": f"BLOCKEDBY#{user_id}"})
            elif sk == "TELEGRAM":  # the chat -> account lookup lives outside my partition
                self._table.delete_item(Key={"pk": f"TGCHAT#{item['chat_id']}", "sk": "LINK"})
            elif sk.startswith("BLOCKEDBY#"):
                other = sk.removeprefix("BLOCKEDBY#")
                self._table.delete_item(Key={"pk": user_pk(other), "sk": f"BLOCK#{user_id}"})
            self._table.delete_item(Key={"pk": item["pk"], "sk": sk})
        # nothing left to moderate: complaints about this student are closed (kept as history)
        ReportRepository(self._table).close_for_owner(user_id, STATUS_DISMISSED, DELETED_BY)
        return photos
