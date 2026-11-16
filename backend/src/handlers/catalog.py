"""GET /books — the main-page catalog: other students' books, newest first.

Query parameters (all optional): q (title/author words), genre, language, offer (give|exchange).
Each book comes with its owner's display name so the cabinet can say whose shelf it is from.
"""

from common.db import main_table
from common.http import api_handler, current_user
from domain.catalog import CatalogFilter
from repositories.catalog import CatalogRepository
from repositories.profiles import ProfileRepository

MAX_RESULTS = 300


def get_repos() -> tuple[CatalogRepository, ProfileRepository]:
    table = main_table()
    return CatalogRepository(table), ProfileRepository(table)


@api_handler
def list_handler(event, context):
    viewer_id, _ = current_user(event)
    flt = CatalogFilter.from_query(event.get("queryStringParameters"))
    catalog, profiles = get_repos()

    found = [b for b in catalog.all_books() if b.owner_id != viewer_id and flt.matches(b)]
    shown = found[:MAX_RESULTS]

    names: dict[str, str] = {}
    for owner_id in {b.owner_id for b in shown}:
        profile = profiles.get(owner_id)
        names[owner_id] = profile.display_name if profile else "Студент УКУ"

    return {
        "books": [{**b.to_json(), "owner_name": names[b.owner_id]} for b in shown],
        "total": len(found),
    }
