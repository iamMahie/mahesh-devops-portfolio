"""Inquiry, Booking and ContactMessage schemas."""

from __future__ import annotations

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import BookingStatus, InquiryStatus, PackageInterest

_PHONE_RE = re.compile(r"^\+?[0-9 \-()]{7,20}$")


def _validate_phone(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if not _PHONE_RE.match(cleaned):
        raise ValueError("phone must contain 7-20 digits and may start with '+'")
    return cleaned


# --------------------------------------------------------------------------- inquiries
class InquiryCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    event_date: date | None = None
    location: str | None = Field(default=None, max_length=200)
    package_interest: PackageInterest | None = None
    message: str | None = Field(default=None, max_length=5000)

    _check_phone = field_validator("phone")(_validate_phone)

    @field_validator("event_date")
    @classmethod
    def _event_date_not_in_past(cls, value: date | None) -> date | None:
        if value and value < date.today():
            raise ValueError("event_date cannot be in the past")
        return value


class InquiryStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: InquiryStatus


class InquiryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    email: EmailStr
    phone: str | None
    event_date: date | None
    location: str | None
    package_interest: PackageInterest | None
    message: str | None
    status: InquiryStatus
    created_at: datetime


# --------------------------------------------------------------------------- bookings
class BookingCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    booking_date: date
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("booking_date")
    @classmethod
    def _booking_date_in_future(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("booking_date must be today or later")
        return value


class BookingStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BookingStatus


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    email: EmailStr
    booking_date: date
    notes: str | None
    status: BookingStatus
    created_at: datetime


# --------------------------------------------------------------------------- contact
class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=5000)


class ContactMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    subject: str
    message: str
    is_read: bool
    created_at: datetime
