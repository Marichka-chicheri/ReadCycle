"""Shared HTTP helpers: JSON responses and a single error format.

Every error body looks like: {"error": {"code": "NOT_FOUND", "message": "..."}}
CORS headers are added by API Gateway (cors_configuration), not here.
"""

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


def json_response(status: int, body: Any) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def error_response(status: int, code: str, message: str) -> dict:
    return json_response(status, {"error": {"code": code, "message": message}})


def claims(event: dict) -> dict:
    """JWT claims validated by the API Gateway Cognito authorizer."""
    return event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})


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
            return error_response(e.status, e.code, e.message)
        except Exception:
            logger.exception("Unhandled error")
            return error_response(500, "INTERNAL_ERROR", "Internal server error")

    return wrapper
