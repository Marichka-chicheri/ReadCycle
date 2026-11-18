"""Who receives Telegram notifications. Key layout (main table):

link code:  pk=TGCODE#<code>   sk=LINK      user_id, created_at   one-time, ~15 minutes
user:       pk=USER#<id>       sk=TELEGRAM  chat_id, linked_at
chat:       pk=TGCHAT#<chat>   sk=LINK      user_id               reverse lookup for /stop

Linking: the profile asks for a code and opens t.me/<bot>?start=<code>; the student presses
Start, Telegram sends "/start <code>" to our webhook, and the code tells us whose chat it is.
"""

import secrets
from datetime import UTC, datetime, timedelta

from common.db import user_pk
from domain.profile import now_iso

CODE_TTL = timedelta(minutes=15)


def _chat_pk(chat_id: str) -> str:
    return f"TGCHAT#{chat_id}"


class TelegramRepository:
    def __init__(self, table):
        self._table = table

    # ----- one-time link codes -----

    def new_code(self, user_id: str) -> str:
        code = secrets.token_urlsafe(16)  # A-Z a-z 0-9 _ - : allowed in a t.me start parameter
        self._table.put_item(
            Item={"pk": f"TGCODE#{code}", "sk": "LINK", "user_id": user_id, "created_at": now_iso()}
        )
        return code

    def use_code(self, code: str) -> str | None:
        """The user id behind a fresh code (the code is spent), or None."""
        key = {"pk": f"TGCODE#{code}", "sk": "LINK"}
        item = self._table.get_item(Key=key).get("Item")
        if not item:
            return None
        self._table.delete_item(Key=key)
        created = datetime.fromisoformat(item["created_at"])
        return item["user_id"] if datetime.now(UTC) - created <= CODE_TTL else None

    # ----- linked chats -----

    def chat_id(self, user_id: str) -> str | None:
        item = self._table.get_item(Key={"pk": user_pk(user_id), "sk": "TELEGRAM"}).get("Item")
        return str(item["chat_id"]) if item else None

    def link(self, user_id: str, chat_id: str) -> None:
        """One chat <-> one account: relinking moves it."""
        self.unlink_user(user_id)
        self.unlink_chat(chat_id)
        self._table.put_item(
            Item={
                "pk": user_pk(user_id),
                "sk": "TELEGRAM",
                "chat_id": chat_id,
                "linked_at": now_iso(),
            }
        )
        self._table.put_item(Item={"pk": _chat_pk(chat_id), "sk": "LINK", "user_id": user_id})

    def unlink_user(self, user_id: str) -> None:
        chat = self.chat_id(user_id)
        if chat:
            self._table.delete_item(Key={"pk": _chat_pk(chat), "sk": "LINK"})
        self._table.delete_item(Key={"pk": user_pk(user_id), "sk": "TELEGRAM"})

    def unlink_chat(self, chat_id: str) -> str | None:
        """Unlink whoever uses this chat; returns their user id."""
        item = self._table.get_item(Key={"pk": _chat_pk(chat_id), "sk": "LINK"}).get("Item")
        if not item:
            return None
        self._table.delete_item(Key={"pk": user_pk(item["user_id"]), "sk": "TELEGRAM"})
        self._table.delete_item(Key={"pk": _chat_pk(chat_id), "sk": "LINK"})
        return item["user_id"]
