"""The signed-in user's wishlist.

GET    /my/wishes        — list
POST   /my/wishes        — add a wish
PUT    /my/wishes/{id}   — edit a wish
DELETE /my/wishes/{id}   — remove a wish
"""

from common.crud import OwnedCollectionApi
from common.db import main_table
from common.http import api_handler
from domain.wish import Wish
from repositories.wishes import MAX_WISHES_PER_USER, WishRepository


def get_repo() -> WishRepository:
    return WishRepository(main_table())


collection = OwnedCollectionApi(
    repo_factory=lambda: get_repo(),
    entity=Wish,
    name="wish",
    plural="wishes",
    limit=MAX_WISHES_PER_USER,
    not_found="Бажання не знайдено",
    limit_message=f"Не більше {MAX_WISHES_PER_USER} позицій у вішлісті",
)

list_handler = api_handler(collection.list)
create_handler = api_handler(collection.create)
update_handler = api_handler(collection.update)
delete_handler = api_handler(collection.delete)
