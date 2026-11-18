"""Talking to the Telegram Bot API (stdlib only).

The bot token comes from the TELEGRAM_BOT_TOKEN env var (GitHub secret -> Terraform -> Lambda).
Without it the bot is simply switched off: the profile does not offer it and nothing is sent.

Telegram calls our webhook (POST /telegram/webhook) with the header
X-Telegram-Bot-Api-Secret-Token = webhook_secret(); infra/deploy.sh registers the webhook
with the same value, so nobody else can pretend to be Telegram.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

API = "https://api.telegram.org"
TIMEOUT_SECONDS = 4

_username_cache: dict[str, str] = {}


def bot_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def enabled() -> bool:
    return bool(bot_token())


def webhook_secret() -> str:
    """Derived from the token, so no second secret has to be configured (deploy.sh does the same:
    printf %s "$TOKEN" | sha256sum | cut -c1-48)."""
    return hashlib.sha256(bot_token().encode()).hexdigest()[:48]


def _call(method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{API}/bot{bot_token()}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:  # noqa: S310 - fixed host
        return json.loads(resp.read().decode("utf-8"))


def bot_username() -> str:
    """@username of the bot (asked once per Lambda container)."""
    token = bot_token()
    if token not in _username_cache:
        _username_cache[token] = _call("getMe", {}).get("result", {}).get("username", "")
    return _username_cache[token]


def send_message(chat_id: str, text: str, button: tuple[str, str] | None = None) -> bool:
    """Send an HTML message; `button` = (label, url). Never raises: returns False on failure."""
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if button:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": button[0], "url": button[1]}]]}
    try:
        return bool(_call("sendMessage", payload).get("ok"))
    except Exception as e:  # noqa: BLE001 - a blocked bot or a timeout must not break anything
        log.warning("telegram sendMessage to %s failed: %s", chat_id, e)
        return False
