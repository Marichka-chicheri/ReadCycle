"""Cognito Pre Sign-up trigger: only emails from ALLOWED_EMAIL_DOMAIN may register, and not an
email a moderator has banned (otherwise a banned student could delete the account and sign up
again with the same address).

It runs for email/password sign-ups and, when Google sign-in is on (GOOGLE_SIGNIN=1), for Google
logins too. For Google it additionally:
  * requires Google to say the email is verified (an unverified address could belong to anyone);
  * links the Google login to an existing email/password account with the same address, so a
    student never ends up with two profiles;
  * blocks a later email/password sign-up for an address that already signed in with Google.
"""

import logging
import os

# The frontend matches these codes to show a friendly message.
ERROR_CODE = "EMAIL_DOMAIN_NOT_ALLOWED"
BANNED_CODE = "EMAIL_BANNED"
NOT_VERIFIED_CODE = "EMAIL_NOT_VERIFIED"
USES_GOOGLE_CODE = "EMAIL_USES_GOOGLE"

EXTERNAL_PROVIDER = "PreSignUp_ExternalProvider"

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


def _cognito():
    import boto3

    return boto3.client("cognito-idp")


def _users_with_email(pool_id: str, email: str) -> list[dict]:
    """All pool users with this email. Cognito's filter is case-sensitive, so try both spellings."""
    found: dict[str, dict] = {}
    for variant in dict.fromkeys([email, email.lower()]):
        quoted = variant.replace("\\", "\\\\").replace('"', '\\"')
        resp = _cognito().list_users(UserPoolId=pool_id, Filter=f'email = "{quoted}"', Limit=10)
        for user in resp.get("Users", []):
            found[user["Username"]] = user
    return list(found.values())


def _link_to_existing_user(event: dict, email: str) -> None:
    """Attach this Google login to the confirmed email/password user with the same email."""
    pool_id = event["userPoolId"]
    provider, _, subject = event["userName"].partition("_")  # "Google_1234" -> Google, 1234
    for user in _users_with_email(pool_id, email):
        if user.get("UserStatus") != "CONFIRMED":
            continue
        _cognito().admin_link_provider_for_user(
            UserPoolId=pool_id,
            DestinationUser={"ProviderName": "Cognito", "ProviderAttributeValue": user["Username"]},
            SourceUser={
                "ProviderName": provider,
                "ProviderAttributeName": "Cognito_Subject",
                "ProviderAttributeValue": subject,
            },
        )
        log.info("Linked %s login to existing user", provider)
        return


def _has_google_account(event: dict, email: str) -> bool:
    return any(
        u.get("UserStatus") == "EXTERNAL_PROVIDER"
        for u in _users_with_email(event["userPoolId"], email)
    )


def handler(event, context):
    domain = os.environ.get("ALLOWED_EMAIL_DOMAIN", "ucu.edu.ua")
    attrs = event.get("request", {}).get("userAttributes", {})
    email = attrs.get("email", "")
    external = event.get("triggerSource") == EXTERNAL_PROVIDER

    if not is_allowed(email, domain):
        # Raising rejects the sign-up; Cognito returns "PreSignUp failed with error <msg>."
        raise Exception(f"{ERROR_CODE}: only @{domain} emails can register")
    if is_banned(email):
        raise Exception(f"{BANNED_CODE}: this email was banned by a moderator")

    if os.environ.get("GOOGLE_SIGNIN"):
        if external:
            if str(attrs.get("email_verified", "")).lower() != "true":
                raise Exception(f"{NOT_VERIFIED_CODE}: Google has not verified this email")
            _link_to_existing_user(event, email)
        elif _has_google_account(event, email):
            raise Exception(f"{USES_GOOGLE_CODE}: this email signs in with Google")
    return event
