"""Gallery image endpoints (all writes are admin-protected)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, status

from app.api.deps import CurrentAdmin, GalleryServiceDep
from app.schemas.gallery import (
    GalleryImageCreate,
    GalleryImageRead,
    GalleryImageReorder,
    GalleryImageUpdate,
)

router = APIRouter(tags=["gallery"])


@router.get(
    "/portfolios/{portfolio_id}/images",
    response_model=list[GalleryImageRead],
    summary="List images of a portfolio",
)
async def list_images(
    portfolio_id: Annotated[int, Path(gt=0)],
    service: GalleryServiceDep,
) -> list[GalleryImageRead]:
    rows = await service.list_images(portfolio_id)
    return [GalleryImageRead.model_validate(row) for row in rows]


@router.post(
    "/portfolios/{portfolio_id}/images",
    response_model=GalleryImageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an image to a portfolio (admin)",
)
async def add_image(
    portfolio_id: Annotated[int, Path(gt=0)],
    payload: GalleryImageCreate,
    service: GalleryServiceDep,
    _: CurrentAdmin,
) -> GalleryImageRead:
    payload = payload.model_copy(update={"portfolio_id": portfolio_id})
    return GalleryImageRead.model_validate(await service.add_image(payload))


@router.put(
    "/portfolios/{portfolio_id}/images/reorder",
    response_model=list[GalleryImageRead],
    summary="Reorder gallery images (admin)",
)
async def reorder_images(
    portfolio_id: Annotated[int, Path(gt=0)],
    payload: GalleryImageReorder,
    service: GalleryServiceDep,
    _: CurrentAdmin,
) -> list[GalleryImageRead]:
    rows = await service.reorder(portfolio_id, payload)
    return [GalleryImageRead.model_validate(row) for row in rows]


@router.put(
    "/portfolios/{portfolio_id}/images/{image_id}/feature",
    response_model=GalleryImageRead,
    summary="Use this image as the portfolio cover (admin)",
)
async def set_featured_image(
    portfolio_id: Annotated[int, Path(gt=0)],
    image_id: Annotated[int, Path(gt=0)],
    service: GalleryServiceDep,
    _: CurrentAdmin,
) -> GalleryImageRead:
    return GalleryImageRead.model_validate(
        await service.set_featured_image(portfolio_id, image_id)
    )


@router.patch(
    "/images/{image_id}", response_model=GalleryImageRead, summary="Update an image (admin)"
)
async def update_image(
    image_id: Annotated[int, Path(gt=0)],
    payload: GalleryImageUpdate,
    service: GalleryServiceDep,
    _: CurrentAdmin,
) -> GalleryImageRead:
    return GalleryImageRead.model_validate(await service.update_image(image_id, payload))


@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete an image (admin)",
)
async def delete_image(
    image_id: Annotated[int, Path(gt=0)],
    service: GalleryServiceDep,
    _: CurrentAdmin,
) -> None:
    await service.delete_image(image_id)
