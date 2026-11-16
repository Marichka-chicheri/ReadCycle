import json

import pytest


class FakeTable:
    """In-memory stand-in for a boto3 DynamoDB Table (only the calls the repositories use)."""

    def __init__(self):
        self.items: dict[tuple[str, str], dict] = {}

    def get_item(self, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {"Item": dict(item)} if item else {}

    def put_item(self, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}


@pytest.fixture
def table():
    return FakeTable()


def make_event(sub="user-1", email="anna@ucu.edu.ua", body=None):
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {"sub": sub, "email": email}}}}}
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def body_of(resp):
    return json.loads(resp["body"])
