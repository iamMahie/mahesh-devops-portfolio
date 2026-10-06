from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.pagination import Page, PaginationParams
from app.models.content import Reel
from app.repositories.content import ReelRepository, SiteContentRepository
from app.schemas.content import ReelInput, ReelRead, SiteContentInput


def default_business() -> dict[str, str]:
    return {
        "name": "WedStudiozs",
        "phone": settings.business_phone,
        "email": settings.business_email,
        "address": settings.business_address,
        "footer_text": "Wedding photography and films. The people, the feeling, the moments in between.",
        "instagram_handle": "wed_studiozs",
    }


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.reels = ReelRepository(session)
        self.details = SiteContentRepository(session)

    async def business(self) -> dict[str, str]:
        business = default_business()
        content = await self.details.get(1)
        if content:
            business.update(SiteContentInput.model_validate(content).model_dump())
        return business

    async def save_details(self, payload: SiteContentInput) -> None:
        content = await self.details.get(1)
        if content:
            await self.details.update(content, payload.model_dump())
        else:
            await self.details.create(id=1, **payload.model_dump())
        await self.session.commit()

    async def list_reels(self, pagination: PaginationParams, *, public: bool = False) -> Page[ReelRead]:
        statement = self.reels.ordered(public=public)
        items = await self.reels.list(
            statement=statement, offset=pagination.offset, limit=pagination.limit,
        )
        return Page[ReelRead].create(
            [ReelRead.model_validate(item) for item in items],
            await self.reels.count(statement), pagination,
        )

    async def get_reel(self, reel_id: int) -> Reel:
        reel = await self.reels.get(reel_id)
        if reel is None:
            raise NotFoundError("That film no longer exists. Return to the film list.")
        return reel

    async def save_reel(self, payload: ReelInput, reel_id: int | None = None) -> None:
        if reel_id is None:
            await self.reels.create(**payload.model_dump())
        else:
            await self.reels.update(await self.get_reel(reel_id), payload.model_dump())
        await self.session.commit()

    async def delete_reel(self, reel_id: int) -> None:
        await self.reels.delete(await self.get_reel(reel_id))
        await self.session.commit()
