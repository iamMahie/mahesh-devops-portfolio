"""Inquiry, Booking and ContactMessage business rules."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import Page, PaginationParams
from app.models.crm import Booking, ContactMessage, Inquiry
from app.models.enums import BookingStatus, InquiryStatus
from app.repositories.crm import (
    BookingRepository,
    ContactMessageRepository,
    InquiryRepository,
)
from app.schemas.crm import (
    BookingCreate,
    BookingRead,
    ContactMessageCreate,
    ContactMessageRead,
    InquiryCreate,
    InquiryRead,
)

# Statuses a lead may move to, keyed by its current status.
_INQUIRY_TRANSITIONS: dict[InquiryStatus, set[InquiryStatus]] = {
    InquiryStatus.NEW: {InquiryStatus.CONTACTED, InquiryStatus.LOST},
    InquiryStatus.CONTACTED: {InquiryStatus.QUOTED, InquiryStatus.LOST},
    InquiryStatus.QUOTED: {InquiryStatus.WON, InquiryStatus.LOST},
    InquiryStatus.WON: set(),
    InquiryStatus.LOST: set(),
}

_BOOKING_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
}


class InquiryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InquiryRepository(session)

    async def submit(self, payload: InquiryCreate) -> Inquiry:
        inquiry = await self.repo.create(
            **payload.model_dump(), status=InquiryStatus.NEW
        )
        await self.session.commit()
        await self.session.refresh(inquiry)
        return inquiry

    async def list_inquiries(
        self,
        params: PaginationParams,
        *,
        status: InquiryStatus | None = None,
        search: str | None = None,
        event_from: date | None = None,
        event_to: date | None = None,
    ) -> Page[InquiryRead]:
        if event_from and event_to and event_from > event_to:
            raise ValidationError("event_from must be earlier than event_to.")
        stmt = self.repo.build_query(
            status=status, search=search, event_from=event_from, event_to=event_to
        )
        total = await self.repo.count(stmt)
        rows = await self.repo.list(
            offset=params.offset,
            limit=params.limit,
            order_by=Inquiry.created_at.desc(),
            statement=stmt,
        )
        return Page.create([InquiryRead.model_validate(r) for r in rows], total, params)

    async def get(self, inquiry_id: int) -> Inquiry:
        inquiry = await self.repo.get(inquiry_id)
        if inquiry is None:
            raise NotFoundError(f"Inquiry {inquiry_id} was not found.")
        return inquiry

    async def change_status(self, inquiry_id: int, new_status: InquiryStatus) -> Inquiry:
        inquiry = await self.get(inquiry_id)
        allowed = _INQUIRY_TRANSITIONS[inquiry.status]
        if new_status != inquiry.status and new_status not in allowed:
            raise ConflictError(
                f"Cannot move inquiry from '{inquiry.status}' to '{new_status}'.",
                details={"allowed": sorted(allowed)},
            )
        inquiry.status = new_status
        await self.session.commit()
        await self.session.refresh(inquiry)
        return inquiry

    async def delete(self, inquiry_id: int) -> None:
        inquiry = await self.get(inquiry_id)
        await self.repo.delete(inquiry)
        await self.session.commit()


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BookingRepository(session)

    async def request(self, payload: BookingCreate) -> Booking:
        if await self.repo.slot_taken(payload.booking_date, payload.email):
            raise ConflictError(
                "You already have an active consultation request for that date."
            )
        booking = await self.repo.create(**payload.model_dump(), status=BookingStatus.PENDING)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def list_bookings(
        self,
        params: PaginationParams,
        *,
        status: BookingStatus | None = None,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> Page[BookingRead]:
        if date_from and date_to and date_from > date_to:
            raise ValidationError("date_from must be earlier than date_to.")
        stmt = self.repo.build_query(
            status=status, search=search, date_from=date_from, date_to=date_to
        )
        total = await self.repo.count(stmt)
        rows = await self.repo.list(
            offset=params.offset,
            limit=params.limit,
            order_by=Booking.booking_date.asc(),
            statement=stmt,
        )
        return Page.create([BookingRead.model_validate(r) for r in rows], total, params)

    async def get(self, booking_id: int) -> Booking:
        booking = await self.repo.get(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking {booking_id} was not found.")
        return booking

    async def change_status(self, booking_id: int, new_status: BookingStatus) -> Booking:
        booking = await self.get(booking_id)
        allowed = _BOOKING_TRANSITIONS[booking.status]
        if new_status != booking.status and new_status not in allowed:
            raise ConflictError(
                f"Cannot move booking from '{booking.status}' to '{new_status}'.",
                details={"allowed": sorted(allowed)},
            )
        booking.status = new_status
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def delete(self, booking_id: int) -> None:
        booking = await self.get(booking_id)
        await self.repo.delete(booking)
        await self.session.commit()


class ContactService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContactMessageRepository(session)

    async def submit(self, payload: ContactMessageCreate) -> ContactMessage:
        message = await self.repo.create(**payload.model_dump())
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def list_messages(
        self,
        params: PaginationParams,
        *,
        search: str | None = None,
        is_read: bool | None = None,
    ) -> Page[ContactMessageRead]:
        stmt = self.repo.build_query(search=search, is_read=is_read)
        total = await self.repo.count(stmt)
        rows = await self.repo.list(
            offset=params.offset,
            limit=params.limit,
            order_by=ContactMessage.created_at.desc(),
            statement=stmt,
        )
        return Page.create([ContactMessageRead.model_validate(r) for r in rows], total, params)

    async def get(self, message_id: int) -> ContactMessage:
        message = await self.repo.get(message_id)
        if message is None:
            raise NotFoundError(f"Contact message {message_id} was not found.")
        return message

    async def mark_read(self, message_id: int, is_read: bool = True) -> ContactMessage:
        message = await self.get(message_id)
        message.is_read = is_read
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def delete(self, message_id: int) -> None:
        message = await self.get(message_id)
        await self.repo.delete(message)
        await self.session.commit()
