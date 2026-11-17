"""GET /matches — people the signed-in user could exchange books with, best first."""

from common.db import main_table
from common.http import api_handler, current_user
from domain.matching import find_matches
from repositories.catalog import CatalogRepository
from repositories.profiles import ProfileRepository

MAX_MATCHES = 30


def get_repos() -> tuple[CatalogRepository, ProfileRepository]:
    table = main_table()
    return CatalogRepository(table), ProfileRepository(table)


@api_handler
def handler(event, context):
    viewer_id, _ = current_user(event)
    catalog, profiles = get_repos()
    books, wishes = catalog.all_books(), catalog.all_wishes()

    result = []
    for match in find_matches(viewer_id, books, wishes):
        profile = profiles.get(match.user_id)
        if not profile:  # signed up but never finished onboarding: nobody to contact
            continue
        result.append(
            {
                "user": profile.to_summary_json(),
                "kind": match.kind,
                "score": match.score,
                "they_have": [m.to_json() for m in match.they_have],
                "they_want": [m.to_json() for m in match.they_want],
            }
        )
        if len(result) >= MAX_MATCHES:
            break

    return {
        "matches": result,
        "my_books": sum(1 for b in books if b.owner_id == viewer_id),
        "my_wishes": sum(1 for w in wishes if w.owner_id == viewer_id),
    }
