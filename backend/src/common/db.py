"""Access to the single DynamoDB table (env TABLE_NAME, keys pk/sk).

boto3 is imported lazily so that unit tests (which use an in-memory fake table) do not need it.
"""

import os
from functools import cache


@cache
def main_table():
    import boto3

    return boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def user_pk(user_id: str) -> str:
    return f"USER#{user_id}"


# Global secondary index over every book / wish (see infra/modules/data): gsi1pk = "BOOK" | "WISH".
CATALOG_INDEX = "gsi1"
