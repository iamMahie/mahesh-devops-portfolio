"""Studio-managed films and public contact information."""

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Reel(Base, TimestampMixin):
    __tablename__ = "reels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    video_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    poster_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    captions_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SiteContent(Base, TimestampMixin):
    __tablename__ = "site_content"
    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    footer_text: Mapped[str] = mapped_column(String(300), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    instagram_handle: Mapped[str] = mapped_column(String(30), nullable=False)
