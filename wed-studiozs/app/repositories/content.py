from sqlalchemy import select

from app.models.content import Reel, SiteContent
from app.repositories.base import BaseRepository


class ReelRepository(BaseRepository[Reel]):
    model = Reel

    @staticmethod
    def ordered(*, public: bool = False):
        statement = select(Reel)
        if public:
            statement = statement.where(Reel.is_published.is_(True))
        return statement.order_by(Reel.display_order, Reel.id)


class SiteContentRepository(BaseRepository[SiteContent]):
    model = SiteContent
