"""GET /health — public liveness check."""

from common.http import api_handler


@api_handler
def handler(event, context):
    return {"status": "ok"}
