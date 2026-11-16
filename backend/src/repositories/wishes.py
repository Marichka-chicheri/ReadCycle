from domain.wish import Wish
from repositories.base import OwnedItemRepository

MAX_WISHES_PER_USER = 50


class WishRepository(OwnedItemRepository[Wish]):
    """A user's wishlist: pk=USER#<owner>, sk=WISH#<id>."""

    prefix = "WISH"
    entity = Wish
