"""Inquiry / Booking / ContactMessage data access."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Select, or_, select

from app.models.crm import Booking, ContactMessage, Inquiry
from app.models.enums import BookingStatus, InquiryStatus
from app.repositories.base import BaseRepository


class InquiryRepository(BaseRepository[Inquiry]):
    model = Inquiry

    def build_query(
        self,
        *,
        status: InquiryStatus | None = None,
        search: str | None = None,
        event_from: date | None = None,
        event_to: date | None = None,
    ) -> Select:
        stmt = select(Inquiry)
        if status is not None:
            stmt = stmt.where(Inquiry.status == status)
        if event_from is not None:
            stmt = stmt.where(Inquiry.event_date >= event_from)
        if event_to is not None:
            stmt = stmt.where(Inquiry.event_date <= event_to)
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    Inquiry.customer_name.ilike(pattern),
                    Inquiry.email.ilike(pattern),
                    Inquiry.location.ilike(pattern),
                    Inquiry.message.ilike(pattern),
                )
            )
        return stmt


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    def build_query(
        self,
        *,
        status: BookingStatus | None = None,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> Select:
        stmt = select(Booking)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        if date_from is not None:
            stmt = stmt.where(Booking.booking_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Booking.booking_date <= date_to)
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(Booking.customer_name.ilike(pattern), Booking.email.ilike(pattern))
            )
        return stmt

    async def slot_taken(self, booking_date: date, email: str) -> bool:
        stmt = (
            select(Booking.id)
            .where(Booking.booking_date == booking_date)
            .where(Booking.email == email)
            .where(Booking.status != BookingStatus.CANCELLED)
            .limit(1)
        )
        return await self.session.scalar(stmt) is not None


class ContactMessageRepository(BaseRepository[ContactMessage]):
    model = ContactMessage

    def build_query(self, *, search: str | None = None, is_read: bool | None = None) -> Select:
        stmt = select(ContactMessage)
        if is_read is not None:
            stmt = stmt.where(ContactMessage.is_read.is_(is_read))
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    ContactMessage.name.ilike(pattern),
                    ContactMessage.email.ilike(pattern),
                    ContactMessage.subject.ilike(pattern),
                    ContactMessage.message.ilike(pattern),
                )
            )
        return stmt
