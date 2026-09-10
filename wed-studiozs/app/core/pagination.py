"""Reusable pagination primitives shared by every list endpoint."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.config import settings

T = TypeVar("T")


@dataclass(slots=True, frozen=True)
class PaginationParams:
    """Injected via `Depends` into routers; keeps offset math in one place."""

    page: int = 1
    size: int = settings.default_page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class Page(BaseModel, Generic[T]):
    """Envelope returned by every paginated endpoint."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> Page[T]:
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=math.ceil(total / params.size) if params.size else 0,
        )
