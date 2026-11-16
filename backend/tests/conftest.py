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

    def delete_item(self, Key):
        self.items.pop((Key["pk"], Key["sk"]), None)
        return {}

    def query(self, KeyConditionExpression, ExpressionAttributeValues, **kwargs):
        # Supports the two patterns the repositories use.
        if kwargs.get("IndexName") == "gsi1":
            assert KeyConditionExpression == "gsi1pk = :pk"
            found = [
                dict(i)
                for i in self.items.values()
                if i.get("gsi1pk") == ExpressionAttributeValues[":pk"]
            ]
            found.sort(key=lambda i: i["gsi1sk"], reverse=not kwargs.get("ScanIndexForward", True))
            return {"Items": found}
        assert KeyConditionExpression == "pk = :pk AND begins_with(sk, :prefix)"
        pk, prefix = ExpressionAttributeValues[":pk"], ExpressionAttributeValues[":prefix"]
        found = [
            dict(item)
            for (ipk, isk), item in sorted(self.items.items())
            if ipk == pk and isk.startswith(prefix)
        ]
        return {"Items": found}


@pytest.fixture
def table():
    return FakeTable()


def make_event(sub="user-1", email="anna@ucu.edu.ua", body=None, path=None):
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {"sub": sub, "email": email}}}}}
    if path is not None:
        event["pathParameters"] = path
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def body_of(resp):
    return json.loads(resp["body"])
