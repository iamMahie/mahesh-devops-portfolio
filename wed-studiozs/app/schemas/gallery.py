"""GalleryImage schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.media import validate_image_url


class GalleryImageBase(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)
    title: str | None = Field(default=None, max_length=200)
    display_order: int = Field(default=0, ge=0, le=10_000)

    _check_image = field_validator("image_url")(validate_image_url)


class GalleryImageCreateNested(GalleryImageBase):
    """Used when images are supplied inline with a portfolio."""


class GalleryImageCreate(GalleryImageBase):
    portfolio_id: int = Field(gt=0)


class GalleryImageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_url: str | None = Field(default=None, min_length=1, max_length=500)
    title: str | None = Field(default=None, max_length=200)
    display_order: int | None = Field(default=None, ge=0, le=10_000)

    _check_image = field_validator("image_url")(validate_image_url)

    @field_validator("image_url", "display_order", mode="before")
    @classmethod
    def _non_nullable_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be empty.")
        return value


class GalleryImageRead(GalleryImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    portfolio_id: int


class GalleryImageReorderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0, le=10_000)


class GalleryImageReorder(BaseModel):
    items: list[GalleryImageReorderItem] = Field(min_length=1)
