"""Portfolio + GalleryImage schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PortfolioCategory
from app.schemas.gallery import GalleryImageCreateNested, GalleryImageRead
from app.schemas.media import validate_image_url


class PortfolioBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category: PortfolioCategory
    cover_image_url: str | None = Field(default=None, max_length=500)
    is_featured: bool = False

    _check_cover = field_validator("cover_image_url")(validate_image_url)

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PortfolioCreate(PortfolioBase):
    slug: str | None = Field(
        default=None,
        max_length=220,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Auto-generated from the title when omitted.",
    )
    images: list[GalleryImageCreateNested] = Field(default_factory=list)


class PortfolioUpdate(BaseModel):
    """All fields optional -> PATCH semantics."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    slug: str | None = Field(default=None, max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=5000)
    category: PortfolioCategory | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    is_featured: bool | None = None

    _check_cover = field_validator("cover_image_url")(validate_image_url)

    @field_validator("title", "slug", "category", "is_featured", mode="before")
    @classmethod
    def _non_nullable_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be empty.")
        return value.strip() if isinstance(value, str) else value


class PortfolioSummary(BaseModel):
    """Lightweight shape used in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    category: PortfolioCategory
    cover_image_url: str | None
    is_featured: bool
    created_at: datetime


class PortfolioRead(PortfolioSummary):
    description: str | None
    updated_at: datetime
    images: list[GalleryImageRead] = Field(default_factory=list)
