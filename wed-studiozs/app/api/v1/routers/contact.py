"""Contact form endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import ContactServiceDep, CurrentAdmin, PaginationDep
from app.core.config import settings
from app.core.pagination import Page
from app.schemas.crm import ContactMessageCreate, ContactMessageRead

router = APIRouter(prefix="/contact", tags=["contact"])


@router.get("/info", summary="Public business contact details")
async def contact_info() -> dict[str, str]:
    return {
        "business_name": settings.app_name,
        "phone": settings.business_phone,
        "email": settings.business_email,
        "address": settings.business_address,
    }


@router.post(
    "/messages",
    response_model=ContactMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Send a contact message (public)",
)
async def submit_message(
    payload: ContactMessageCreate, service: ContactServiceDep
) -> ContactMessageRead:
    return ContactMessageRead.model_validate(await service.submit(payload))


@router.get(
    "/messages", response_model=Page[ContactMessageRead], summary="List messages (admin)"
)
async def list_messages(
    service: ContactServiceDep,
    pagination: PaginationDep,
    _: CurrentAdmin,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    is_read: Annotated[bool | None, Query()] = None,
) -> Page[ContactMessageRead]:
    return await service.list_messages(pagination, search=search, is_read=is_read)


@router.patch(
    "/messages/{message_id}/read",
    response_model=ContactMessageRead,
    summary="Mark a message read/unread (admin)",
)
async def mark_read(
    message_id: Annotated[int, Path(gt=0)],
    service: ContactServiceDep,
    _: CurrentAdmin,
    is_read: Annotated[bool, Query()] = True,
) -> ContactMessageRead:
    return ContactMessageRead.model_validate(await service.mark_read(message_id, is_read))


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a message (admin)",
)
async def delete_message(
    message_id: Annotated[int, Path(gt=0)],
    service: ContactServiceDep,
    _: CurrentAdmin,
) -> None:
    await service.delete(message_id)
