"""Portfolio endpoints: public reads, admin-protected writes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import (
    CurrentAdmin,
    PaginationDep,
    PortfolioServiceDep,
    get_current_admin,
)
from app.core.pagination import Page
from app.models.enums import PortfolioCategory
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioSummary,
    PortfolioUpdate,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=Page[PortfolioSummary], summary="List / search portfolios")
async def list_portfolios(
    service: PortfolioServiceDep,
    pagination: PaginationDep,
    category: Annotated[PortfolioCategory | None, Query(description="Filter by category")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    is_featured: Annotated[bool | None, Query()] = None,
) -> Page[PortfolioSummary]:
    return await service.list_portfolios(
        pagination, category=category, search=search, is_featured=is_featured
    )


@router.get("/featured", response_model=list[PortfolioSummary], summary="Featured work")
async def list_featured(
    service: PortfolioServiceDep,
    limit: Annotated[int, Query(ge=1, le=24)] = 6,
) -> list[PortfolioSummary]:
    rows = await service.list_featured(limit)
    return [PortfolioSummary.model_validate(row) for row in rows]


@router.get("/slug/{slug}", response_model=PortfolioRead, summary="Portfolio detail by slug")
async def get_by_slug(
    service: PortfolioServiceDep,
    slug: Annotated[str, Path(min_length=1, max_length=220)],
) -> PortfolioRead:
    return PortfolioRead.model_validate(await service.get_by_slug(slug))


@router.get("/{portfolio_id}", response_model=PortfolioRead, summary="Portfolio detail by id")
async def get_portfolio(
    service: PortfolioServiceDep,
    portfolio_id: Annotated[int, Path(gt=0)],
) -> PortfolioRead:
    return PortfolioRead.model_validate(await service.get_portfolio(portfolio_id))


@router.post(
    "",
    response_model=PortfolioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
    summary="Create a portfolio (admin)",
)
async def create_portfolio(
    payload: PortfolioCreate, service: PortfolioServiceDep
) -> PortfolioRead:
    return PortfolioRead.model_validate(await service.create_portfolio(payload))


@router.patch("/{portfolio_id}", response_model=PortfolioRead, summary="Update a portfolio (admin)")
async def update_portfolio(
    portfolio_id: Annotated[int, Path(gt=0)],
    payload: PortfolioUpdate,
    service: PortfolioServiceDep,
    _: CurrentAdmin,
) -> PortfolioRead:
    return PortfolioRead.model_validate(await service.update_portfolio(portfolio_id, payload))


@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a portfolio and its gallery (admin)",
)
async def delete_portfolio(
    portfolio_id: Annotated[int, Path(gt=0)],
    service: PortfolioServiceDep,
    _: CurrentAdmin,
) -> None:
    await service.delete_portfolio(portfolio_id)
