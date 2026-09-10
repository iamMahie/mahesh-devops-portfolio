"""Portfolio & gallery business rules (slug uniqueness, ordering, cascades)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import Page, PaginationParams
from app.core.security import slugify
from app.models.enums import PortfolioCategory
from app.models.portfolio import GalleryImage, Portfolio
from app.repositories.portfolio import GalleryImageRepository, PortfolioRepository
from app.schemas.gallery import (
    GalleryImageCreate,
    GalleryImageReorder,
    GalleryImageUpdate,
)
from app.schemas.portfolio import PortfolioCreate, PortfolioSummary, PortfolioUpdate


class PortfolioService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PortfolioRepository(session)
        self.images = GalleryImageRepository(session)

    # ---------------------------------------------------------------- reads
    async def list_portfolios(
        self,
        params: PaginationParams,
        *,
        category: PortfolioCategory | None = None,
        search: str | None = None,
        is_featured: bool | None = None,
    ) -> Page[PortfolioSummary]:
        stmt = self.repo.build_query(category=category, search=search, is_featured=is_featured)
        total = await self.repo.count(stmt)
        rows = await self.repo.list(
            offset=params.offset,
            limit=params.limit,
            order_by=Portfolio.created_at.desc(),
            statement=stmt,
        )
        items = [PortfolioSummary.model_validate(row) for row in rows]
        return Page.create(items, total, params)

    async def get_portfolio(self, portfolio_id: int) -> Portfolio:
        portfolio = await self.repo.get(portfolio_id)
        if portfolio is None:
            raise NotFoundError(f"Portfolio {portfolio_id} was not found.")
        return portfolio

    async def get_by_slug(self, slug: str) -> Portfolio:
        portfolio = await self.repo.get_by_slug(slug)
        if portfolio is None:
            raise NotFoundError(f"Portfolio '{slug}' was not found.")
        return portfolio

    async def list_featured(self, limit: int = 6) -> list[Portfolio]:
        return await self.repo.list_featured(limit)

    # --------------------------------------------------------------- writes
    async def create_portfolio(self, payload: PortfolioCreate) -> Portfolio:
        slug = payload.slug or await self._unique_slug(slugify(payload.title))
        if await self.repo.slug_taken(slug):
            raise ConflictError(f"Slug '{slug}' is already in use.")

        portfolio = Portfolio(
            title=payload.title,
            slug=slug,
            description=payload.description,
            category=payload.category,
            cover_image_url=payload.cover_image_url,
            is_featured=payload.is_featured,
        )
        portfolio.images = [
            GalleryImage(
                image_url=image.image_url,
                title=image.title,
                display_order=(
                    image.display_order if "display_order" in image.model_fields_set else index
                ),
            )
            for index, image in enumerate(payload.images)
        ]
        self.repo.add(portfolio)
        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def update_portfolio(self, portfolio_id: int, payload: PortfolioUpdate) -> Portfolio:
        portfolio = await self.get_portfolio(portfolio_id)
        values = payload.model_dump(exclude_unset=True)

        if "slug" in values and values["slug"]:
            if await self.repo.slug_taken(values["slug"], exclude_id=portfolio_id):
                raise ConflictError(f"Slug '{values['slug']}' is already in use.")
        elif "title" in values and values["title"]:
            values["slug"] = await self._unique_slug(
                slugify(values["title"]), exclude_id=portfolio_id
            )

        await self.repo.update(portfolio, values)
        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def delete_portfolio(self, portfolio_id: int) -> None:
        portfolio = await self.get_portfolio(portfolio_id)
        await self.repo.delete(portfolio)
        await self.session.commit()

    async def _unique_slug(self, base: str, *, exclude_id: int | None = None) -> str:
        slug, suffix = base, 2
        while await self.repo.slug_taken(slug, exclude_id=exclude_id):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug


class GalleryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GalleryImageRepository(session)
        self.portfolios = PortfolioRepository(session)

    async def list_images(self, portfolio_id: int) -> list[GalleryImage]:
        await self._ensure_portfolio(portfolio_id)
        return await self.repo.list_for_portfolio(portfolio_id)

    async def add_image(self, payload: GalleryImageCreate) -> GalleryImage:
        await self._ensure_portfolio(payload.portfolio_id)
        order = (
            payload.display_order if "display_order" in payload.model_fields_set
            else await self.repo.next_display_order(payload.portfolio_id)
        )
        image = await self.repo.create(
            portfolio_id=payload.portfolio_id,
            image_url=payload.image_url,
            title=payload.title,
            display_order=order,
        )
        await self.session.commit()
        await self.session.refresh(image)
        return image

    async def update_image(self, image_id: int, payload: GalleryImageUpdate) -> GalleryImage:
        image = await self._get_image(image_id)
        await self.repo.update(image, payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(image)
        return image

    async def delete_image(self, image_id: int) -> None:
        image = await self._get_image(image_id)
        await self.repo.delete(image)
        await self.session.commit()

    async def reorder(self, portfolio_id: int, payload: GalleryImageReorder) -> list[GalleryImage]:
        await self._ensure_portfolio(portfolio_id)
        existing = {img.id: img for img in await self.repo.list_for_portfolio(portfolio_id)}

        unknown = [item.id for item in payload.items if item.id not in existing]
        if unknown:
            raise ValidationError(
                "Some images do not belong to this portfolio.", details={"image_ids": unknown}
            )

        for item in payload.items:
            existing[item.id].display_order = item.display_order
        await self.session.commit()
        return await self.repo.list_for_portfolio(portfolio_id)

    async def set_featured_image(self, portfolio_id: int, image_id: int) -> GalleryImage:
        """Promote a gallery image to the portfolio cover."""
        portfolio = await self._ensure_portfolio(portfolio_id)
        image = await self._get_image(image_id)
        if image.portfolio_id != portfolio_id:
            raise ValidationError("Image does not belong to the given portfolio.")
        portfolio.cover_image_url = image.image_url
        await self.session.commit()
        return image

    async def _ensure_portfolio(self, portfolio_id: int) -> Portfolio:
        portfolio = await self.portfolios.get(portfolio_id)
        if portfolio is None:
            raise NotFoundError(f"Portfolio {portfolio_id} was not found.")
        return portfolio

    async def _get_image(self, image_id: int) -> GalleryImage:
        image = await self.repo.get(image_id)
        if image is None:
            raise NotFoundError(f"Gallery image {image_id} was not found.")
        return image
