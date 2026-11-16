"""Shared HTTP helpers: JSON responses and a single error format.

Every error body looks like: {"error": {"code": "NOT_FOUND", "message": "..."}}
CORS headers are added by API Gateway (cors_configuration), not here.
"""

import base64
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class ValidationError(ApiError):
    """400 with per-field messages: {"error": {"code": "VALIDATION_ERROR", "message", "fields"}}."""

    def __init__(self, fields: dict[str, str]):
        super().__init__(400, "VALIDATION_ERROR", "Перевірте правильність заповнення полів")
        self.fields = fields


def json_response(status: int, body: Any) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def error_response(status: int, code: str, message: str, fields: dict | None = None) -> dict:
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return json_response(status, {"error": error})


def claims(event: dict) -> dict:
    """JWT claims validated by the API Gateway Cognito authorizer."""
    return event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})


def current_user(event: dict) -> tuple[str, str]:
    """(user_id, email) of the signed-in user. The ID token carries both `sub` and `email`."""
    c = claims(event)
    if not c.get("sub") or not c.get("email"):
        raise ApiError(401, "UNAUTHORIZED", "ID token with email claim required")
    return c["sub"], c["email"]


def json_body(event: dict) -> dict:
    """Parsed JSON object from the request body, or 400."""
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        data = json.loads(raw) if raw else {}
    except ValueError as e:
        raise ApiError(400, "BAD_JSON", "Request body must be valid JSON") from e
    if not isinstance(data, dict):
        raise ApiError(400, "BAD_JSON", "Request body must be a JSON object")
    return data


def api_handler(fn: Callable[[dict, Any], Any]) -> Callable[[dict, Any], dict]:
    """Wrap a handler: return value -> 200 JSON, ApiError -> its status, anything else -> 500."""

    @wraps(fn)
    def wrapper(event: dict, context: Any) -> dict:
        try:
            result = fn(event, context)
            if isinstance(result, dict) and "statusCode" in result:
                return result
            return json_response(200, result)
        except ApiError as e:
            return error_response(e.status, e.code, e.message, getattr(e, "fields", None))
        except Exception:
            logger.exception("Unhandled error")
            return error_response(500, "INTERNAL_ERROR", "Internal server error")

    return wrapper
