"""Customer inquiry endpoints. Submission is public; management is admin-only."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import CurrentAdmin, InquiryServiceDep, PaginationDep
from app.core.pagination import Page
from app.models.enums import InquiryStatus
from app.schemas.crm import InquiryCreate, InquiryRead, InquiryStatusUpdate

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.post(
    "",
    response_model=InquiryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an inquiry (public)",
)
async def submit_inquiry(payload: InquiryCreate, service: InquiryServiceDep) -> InquiryRead:
    return InquiryRead.model_validate(await service.submit(payload))


@router.get("", response_model=Page[InquiryRead], summary="List inquiries (admin)")
async def list_inquiries(
    service: InquiryServiceDep,
    pagination: PaginationDep,
    _: CurrentAdmin,
    status_filter: Annotated[InquiryStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    event_from: Annotated[date | None, Query()] = None,
    event_to: Annotated[date | None, Query()] = None,
) -> Page[InquiryRead]:
    return await service.list_inquiries(
        pagination,
        status=status_filter,
        search=search,
        event_from=event_from,
        event_to=event_to,
    )


@router.get("/{inquiry_id}", response_model=InquiryRead, summary="Inquiry detail (admin)")
async def get_inquiry(
    inquiry_id: Annotated[int, Path(gt=0)],
    service: InquiryServiceDep,
    _: CurrentAdmin,
) -> InquiryRead:
    return InquiryRead.model_validate(await service.get(inquiry_id))


@router.patch(
    "/{inquiry_id}/status", response_model=InquiryRead, summary="Advance inquiry status (admin)"
)
async def update_status(
    inquiry_id: Annotated[int, Path(gt=0)],
    payload: InquiryStatusUpdate,
    service: InquiryServiceDep,
    _: CurrentAdmin,
) -> InquiryRead:
    return InquiryRead.model_validate(await service.change_status(inquiry_id, payload.status))


@router.delete(
    "/{inquiry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete inquiry (admin)",
)
async def delete_inquiry(
    inquiry_id: Annotated[int, Path(gt=0)],
    service: InquiryServiceDep,
    _: CurrentAdmin,
) -> None:
    await service.delete(inquiry_id)
