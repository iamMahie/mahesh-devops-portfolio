"""Portfolio + GalleryImage: the core content aggregate."""

from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import PortfolioCategory

category_enum = Enum(
    PortfolioCategory,
    name="portfolio_category",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"
    __table_args__ = (
        Index("ix_portfolios_category_featured", "category", "is_featured"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[PortfolioCategory] = mapped_column(category_enum, index=True, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    images: Mapped[list[GalleryImage]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="GalleryImage.display_order",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Portfolio id={self.id} slug={self.slug!r}>"


class GalleryImage(Base):
    __tablename__ = "gallery_images"
    __table_args__ = (
        Index("ix_gallery_images_portfolio_order", "portfolio_id", "display_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    portfolio: Mapped[Portfolio] = relationship(back_populates="images")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<GalleryImage id={self.id} portfolio_id={self.portfolio_id}>"
