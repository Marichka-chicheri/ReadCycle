"""Cognito Pre Sign-up trigger: only emails from ALLOWED_EMAIL_DOMAIN may register."""

import os

# The frontend matches this code to show a friendly message.
ERROR_CODE = "EMAIL_DOMAIN_NOT_ALLOWED"


def is_allowed(email: str, domain: str) -> bool:
    email = (email or "").strip().lower()
    return email.count("@") == 1 and email.split("@")[1] == domain.lower()


def handler(event, context):
    domain = os.environ.get("ALLOWED_EMAIL_DOMAIN", "ucu.edu.ua")
    email = event.get("request", {}).get("userAttributes", {}).get("email", "")
    if not is_allowed(email, domain):
        # Raising rejects the sign-up; Cognito returns "PreSignUp failed with error <msg>."
        raise Exception(f"{ERROR_CODE}: only @{domain} emails can register")
    return event
