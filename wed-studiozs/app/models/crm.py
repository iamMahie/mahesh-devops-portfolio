"""Lead-capture models: Inquiry, Booking, ContactMessage."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import BookingStatus, InquiryStatus, PackageInterest

inquiry_status_enum = Enum(
    InquiryStatus,
    name="inquiry_status",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
)
booking_status_enum = Enum(
    BookingStatus,
    name="booking_status",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
)
package_interest_enum = Enum(
    PackageInterest,
    name="package_interest",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
)


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    event_date: Mapped[date | None] = mapped_column(Date, index=True)
    location: Mapped[str | None] = mapped_column(String(200))
    package_interest: Mapped[PackageInterest | None] = mapped_column(package_interest_enum)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[InquiryStatus] = mapped_column(
        inquiry_status_enum, default=InquiryStatus.NEW, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[BookingStatus] = mapped_column(
        booking_status_enum, default=BookingStatus.PENDING, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
