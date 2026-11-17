"""Cognito Pre Sign-up trigger: only emails from ALLOWED_EMAIL_DOMAIN may register, and not an
email a moderator has banned (otherwise a banned student could delete the account and sign up
again with the same address)."""

import logging
import os

# The frontend matches these codes to show a friendly message.
ERROR_CODE = "EMAIL_DOMAIN_NOT_ALLOWED"
BANNED_CODE = "EMAIL_BANNED"

log = logging.getLogger(__name__)


def is_allowed(email: str, domain: str) -> bool:
    email = (email or "").strip().lower()
    return email.count("@") == 1 and email.split("@")[1] == domain.lower()


def is_banned(email: str) -> bool:
    if not os.environ.get("TABLE_NAME"):  # not configured: nothing to check against
        log.warning("TABLE_NAME is not set: banned emails are not checked")
        return False
    from common.db import main_table
    from repositories.moderation import BanRepository

    return BanRepository(main_table()).is_email_banned(email)


def handler(event, context):
    domain = os.environ.get("ALLOWED_EMAIL_DOMAIN", "ucu.edu.ua")
    email = event.get("request", {}).get("userAttributes", {}).get("email", "")
    if not is_allowed(email, domain):
        # Raising rejects the sign-up; Cognito returns "PreSignUp failed with error <msg>."
        raise Exception(f"{ERROR_CODE}: only @{domain} emails can register")
    if is_banned(email):
        raise Exception(f"{BANNED_CODE}: this email was banned by a moderator")
    return event
