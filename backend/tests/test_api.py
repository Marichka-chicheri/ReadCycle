import json

from handlers import health, me


def _body(resp):
    return json.loads(resp["body"])


def test_health():
    resp = health.handler({}, None)
    assert resp["statusCode"] == 200
    assert _body(resp) == {"status": "ok"}


def test_me_returns_email_from_claims():
    event = {
        "requestContext": {
            "authorizer": {"jwt": {"claims": {"sub": "abc", "email": "s@ucu.edu.ua"}}}
        }
    }
    resp = me.handler(event, None)
    assert resp["statusCode"] == 200
    assert _body(resp) == {"sub": "abc", "email": "s@ucu.edu.ua"}


def test_me_without_claims_uses_error_format():
    resp = me.handler({}, None)
    assert resp["statusCode"] == 401
    assert _body(resp)["error"]["code"] == "UNAUTHORIZED"
