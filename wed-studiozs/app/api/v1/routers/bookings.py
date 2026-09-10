"""Consultation booking endpoints."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import BookingServiceDep, CurrentAdmin, PaginationDep
from app.core.pagination import Page
from app.models.enums import BookingStatus
from app.schemas.crm import BookingCreate, BookingRead, BookingStatusUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Request a consultation (public)",
)
async def request_booking(payload: BookingCreate, service: BookingServiceDep) -> BookingRead:
    return BookingRead.model_validate(await service.request(payload))


@router.get("", response_model=Page[BookingRead], summary="List bookings (admin)")
async def list_bookings(
    service: BookingServiceDep,
    pagination: PaginationDep,
    _: CurrentAdmin,
    status_filter: Annotated[BookingStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> Page[BookingRead]:
    return await service.list_bookings(
        pagination,
        status=status_filter,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{booking_id}", response_model=BookingRead, summary="Booking detail (admin)")
async def get_booking(
    booking_id: Annotated[int, Path(gt=0)],
    service: BookingServiceDep,
    _: CurrentAdmin,
) -> BookingRead:
    return BookingRead.model_validate(await service.get(booking_id))


@router.patch(
    "/{booking_id}/status", response_model=BookingRead, summary="Change booking status (admin)"
)
async def update_status(
    booking_id: Annotated[int, Path(gt=0)],
    payload: BookingStatusUpdate,
    service: BookingServiceDep,
    _: CurrentAdmin,
) -> BookingRead:
    return BookingRead.model_validate(await service.change_status(booking_id, payload.status))


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete booking (admin)",
)
async def delete_booking(
    booking_id: Annotated[int, Path(gt=0)],
    service: BookingServiceDep,
    _: CurrentAdmin,
) -> None:
    await service.delete(booking_id)
