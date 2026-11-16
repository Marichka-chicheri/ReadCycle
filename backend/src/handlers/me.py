"""GET /me — returns the signed-in user's identity from the Cognito ID token."""

from common.http import ApiError, api_handler, claims


@api_handler
def handler(event, context):
    c = claims(event)
    if not c.get("email"):
        # Access tokens have no email claim; the frontend must send the ID token.
        raise ApiError(401, "UNAUTHORIZED", "ID token with email claim required")
    return {"sub": c.get("sub"), "email": c["email"]}
