"""Telegram notifications about books from your wishlist.

GET    /telegram          — {available, linked}: is the bot set up, is my Telegram connected
POST   /telegram/link     — {url}: t.me link with a one-time code; pressing Start connects
DELETE /telegram          — stop notifications
POST   /telegram/webhook  — called by Telegram itself (no Cognito; checked by a secret header)
"""

import logging

from common import telegram
from common.db import main_table
from common.http import ApiError, api_handler, current_user, json_body
from repositories.telegram import TelegramRepository

log = logging.getLogger(__name__)

WELCOME = (
    "Готово! Тепер я напишу тобі, щойно на ReadCycle з'явиться книга з твого вішліста. 📚\n\n"
    "Вимкнути сповіщення: /stop або в профілі на сайті."
)
HELP = (
    "Я бот ReadCycle: повідомляю, коли на полиці з'являється книга з твого вішліста.\n\n"
    "Щоб підключитися, відкрий свій профіль на сайті й натисни «Підключити Telegram»."
)
STOPPED = "Сповіщення вимкнено. Увімкнути знову можна в профілі на сайті."
EXPIRED = "Посилання застаріло. Натисни «Підключити Telegram» у профілі ще раз."


def get_repo() -> TelegramRepository:
    return TelegramRepository(main_table())


def _require_bot() -> None:
    if not telegram.enabled():
        raise ApiError(503, "TELEGRAM_OFF", "Telegram-бот ще не налаштований")


@api_handler
def status_handler(event, context):
    user_id, _ = current_user(event)
    if not telegram.enabled():
        return {"available": False, "linked": False}
    return {"available": True, "linked": get_repo().chat_id(user_id) is not None}


@api_handler
def link_handler(event, context):
    user_id, _ = current_user(event)
    _require_bot()
    code = get_repo().new_code(user_id)
    return {"url": f"https://t.me/{telegram.bot_username()}?start={code}"}


@api_handler
def unlink_handler(event, context):
    user_id, _ = current_user(event)
    repo = get_repo()
    chat = repo.chat_id(user_id)
    repo.unlink_user(user_id)
    if chat and telegram.enabled():
        telegram.send_message(chat, STOPPED)
    return {"linked": False}


def _header(event, name: str) -> str:
    return {k.lower(): v for k, v in (event.get("headers") or {}).items()}.get(name, "")


@api_handler
def webhook_handler(event, context):
    if not telegram.enabled() or _header(event, "x-telegram-bot-api-secret-token") != (
        telegram.webhook_secret()
    ):
        raise ApiError(403, "FORBIDDEN", "Forbidden")
    # Always answer 200 to Telegram, or it will keep re-sending the same update.
    try:
        message = json_body(event).get("message") or {}
        chat = message.get("chat") or {}
        if chat.get("type") != "private" or "id" not in chat:
            return {"ok": True}
        chat_id, text = str(chat["id"]), (message.get("text") or "").strip()
        repo = get_repo()

        if text.startswith("/start"):
            code = text.removeprefix("/start").strip()
            if not code:
                telegram.send_message(chat_id, HELP)
            elif user_id := repo.use_code(code):
                repo.link(user_id, chat_id)
                telegram.send_message(chat_id, WELCOME)
            else:
                telegram.send_message(chat_id, EXPIRED)
        elif text.startswith("/stop"):
            repo.unlink_chat(chat_id)
            telegram.send_message(chat_id, STOPPED)
        else:
            telegram.send_message(chat_id, HELP)
    except Exception:  # noqa: BLE001
        log.exception("telegram webhook update failed")
    return {"ok": True}
