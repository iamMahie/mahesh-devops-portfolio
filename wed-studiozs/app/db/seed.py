"""Explicit demo portfolio seeding; never creates accounts or runs on startup."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import slugify
from app.models import GalleryImage, Portfolio, PortfolioCategory

logger = logging.getLogger(__name__)

_DEMO_PORTFOLIOS: list[dict] = [
    {
        "title": "Aarav & Meera - Palace Wedding",
        "category": PortfolioCategory.WEDDINGS,
        "description": "A three-day Rajasthani celebration shot across Udaipur's lake palaces.",
        "cover_image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?w=1200",
        "is_featured": True,
        "images": [
            "https://images.unsplash.com/photo-1606216794074-735e91aa2c92?w=900",
            "https://images.unsplash.com/photo-1583939003579-730e3918a45a?w=900",
            "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=900",
        ],
    },
    {
        "title": "Rohit & Sana - Rooftop Engagement",
        "category": PortfolioCategory.ENGAGEMENTS,
        "description": "Golden-hour engagement session above the Hyderabad skyline.",
        "cover_image_url": "https://images.unsplash.com/photo-1522673607200-164d1b6ce486?w=1200",
        "is_featured": True,
        "images": [
            "https://images.unsplash.com/photo-1591604466107-ec97de577aff?w=900",
            "https://images.unsplash.com/photo-1520854221256-17451cc331bf?w=900",
        ],
    },
    {
        "title": "Coastal Pre-Wedding - Gokarna",
        "category": PortfolioCategory.PRE_WEDDINGS,
        "description": "Barefoot, windswept and unposed - a two-day coastal story.",
        "cover_image_url": "https://images.unsplash.com/photo-1537633552985-df8429e8048b?w=1200",
        "is_featured": False,
        "images": ["https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=900"],
    },
    {
        "title": "Waiting for Ishaan - Maternity",
        "category": PortfolioCategory.MATERNITY,
        "description": "A soft, natural-light maternity session shot in the family home.",
        "cover_image_url": "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=1200",
        "is_featured": False,
        "images": ["https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=900"],
    },
    {
        "title": "TechSummit 2025 - Corporate Event",
        "category": PortfolioCategory.EVENTS,
        "description": "Full-day conference coverage: keynotes, booths and candid networking.",
        "cover_image_url": "https://images.unsplash.com/photo-1511578314322-379afb476865?w=1200",
        "is_featured": True,
        "images": ["https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=900"],
    },
]


async def seed_portfolios(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Portfolio))
    if count:
        return

    for source in _DEMO_PORTFOLIOS:
        data = source.copy()
        images = data.pop("images")
        portfolio = Portfolio(slug=slugify(data["title"]), **data)
        portfolio.images = [
            GalleryImage(image_url=url, title=f"{portfolio.title} #{i}", display_order=i)
            for i, url in enumerate(images, start=1)
        ]
        session.add(portfolio)

    await session.commit()
    logger.info("Seeded %d demo portfolios", len(_DEMO_PORTFOLIOS))
