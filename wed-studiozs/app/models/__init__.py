"""Import every model here so Alembic autogenerate sees the full metadata."""

from app.db.base import Base
from app.models.admin import AdminUser
from app.models.crm import Booking, ContactMessage, Inquiry
from app.models.enums import (
    BookingStatus,
    InquiryStatus,
    PackageInterest,
    PortfolioCategory,
)
from app.models.portfolio import GalleryImage, Portfolio

__all__ = [
    "AdminUser",
    "Base",
    "Booking",
    "BookingStatus",
    "ContactMessage",
    "GalleryImage",
    "Inquiry",
    "InquiryStatus",
    "PackageInterest",
    "Portfolio",
    "PortfolioCategory",
]
