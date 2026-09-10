"""Shared string enums used by both ORM models and Pydantic schemas."""

from enum import StrEnum


class PortfolioCategory(StrEnum):
    WEDDINGS = "weddings"
    ENGAGEMENTS = "engagements"
    PRE_WEDDINGS = "pre_weddings"
    MATERNITY = "maternity"
    EVENTS = "events"

    @property
    def label(self) -> str:
        return self.value.replace("_", "-").title()


class InquiryStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    WON = "won"
    LOST = "lost"


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PackageInterest(StrEnum):
    ESSENTIAL = "essential"
    SIGNATURE = "signature"
    PREMIUM = "premium"
    CUSTOM = "custom"
