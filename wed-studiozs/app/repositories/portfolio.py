"""Portfolio + GalleryImage data access."""

from __future__ import annotations

from sqlalchemy import Select, or_, select

from app.models.enums import PortfolioCategory
from app.models.portfolio import GalleryImage, Portfolio
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    model = Portfolio

    def build_query(
        self,
        *,
        category: PortfolioCategory | None = None,
        search: str | None = None,
        is_featured: bool | None = None,
    ) -> Select:
        """Compose the filter/search statement reused by `list` and `count`."""
        stmt = select(Portfolio)
        if category is not None:
            stmt = stmt.where(Portfolio.category == category)
        if is_featured is not None:
            stmt = stmt.where(Portfolio.is_featured.is_(is_featured))
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    Portfolio.title.ilike(pattern),
                    Portfolio.description.ilike(pattern),
                    Portfolio.slug.ilike(pattern),
                )
            )
        return stmt

    async def get_by_slug(self, slug: str) -> Portfolio | None:
        return await self.session.scalar(select(Portfolio).where(Portfolio.slug == slug))

    async def slug_taken(self, slug: str, *, exclude_id: int | None = None) -> bool:
        stmt = select(Portfolio.id).where(Portfolio.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Portfolio.id != exclude_id)
        return await self.session.scalar(stmt.limit(1)) is not None

    async def list_featured(self, limit: int = 6) -> list[Portfolio]:
        stmt = (
            select(Portfolio)
            .where(Portfolio.is_featured.is_(True))
            .order_by(Portfolio.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.scalars(stmt)).unique().all())


class GalleryImageRepository(BaseRepository[GalleryImage]):
    model = GalleryImage

    async def list_for_portfolio(self, portfolio_id: int) -> list[GalleryImage]:
        stmt = (
            select(GalleryImage)
            .where(GalleryImage.portfolio_id == portfolio_id)
            .order_by(GalleryImage.display_order, GalleryImage.id)
        )
        return list((await self.session.scalars(stmt)).all())

    async def next_display_order(self, portfolio_id: int) -> int:
        images = await self.list_for_portfolio(portfolio_id)
        return (max((img.display_order for img in images), default=-1)) + 1
