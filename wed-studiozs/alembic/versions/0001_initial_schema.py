"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Enum definitions matching the ORM models
from app.models.enums import (
    BookingStatus,
    InquiryStatus,
    PackageInterest,
    PortfolioCategory,
)

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enums (PostgreSQL specific)
    portfolio_category_enum = sa.Enum(
        PortfolioCategory,
        name="portfolio_category",
        values_callable=lambda x: [e.value for e in x],
        native_enum=True,
    )
    portfolio_category_enum.create(op.get_bind(), checkfirst=True)

    inquiry_status_enum = sa.Enum(
        InquiryStatus,
        name="inquiry_status",
        values_callable=lambda x: [e.value for e in x],
        native_enum=True,
    )
    inquiry_status_enum.create(op.get_bind(), checkfirst=True)

    booking_status_enum = sa.Enum(
        BookingStatus,
        name="booking_status",
        values_callable=lambda x: [e.value for e in x],
        native_enum=True,
    )
    booking_status_enum.create(op.get_bind(), checkfirst=True)

    package_interest_enum = sa.Enum(
        PackageInterest,
        name="package_interest",
        values_callable=lambda x: [e.value for e in x],
        native_enum=True,
    )
    package_interest_enum.create(op.get_bind(), checkfirst=True)

    # Create tables
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_users"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.Enum(PortfolioCategory, name="portfolio_category"), nullable=False),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolios"),
    )
    op.create_index("ix_portfolios_slug", "portfolios", ["slug"], unique=True)
    op.create_index("ix_portfolios_category", "portfolios", ["category"])
    op.create_index(
        "ix_portfolios_category_featured", "portfolios", ["category", "is_featured"]
    )

    op.create_table(
        "gallery_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["portfolio_id"],
            ["portfolios.id"],
            name="fk_gallery_images_portfolio_id_portfolios",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_gallery_images"),
    )
    op.create_index("ix_gallery_images_portfolio_id", "gallery_images", ["portfolio_id"])
    op.create_index(
        "ix_gallery_images_portfolio_order",
        "gallery_images",
        ["portfolio_id", "display_order"],
    )

    op.create_table(
        "inquiries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("package_interest", sa.Enum(PackageInterest, name="package_interest"), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum(InquiryStatus, name="inquiry_status"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_inquiries"),
    )
    op.create_index("ix_inquiries_email", "inquiries", ["email"])
    op.create_index("ix_inquiries_event_date", "inquiries", ["event_date"])
    op.create_index("ix_inquiries_status", "inquiries", ["status"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum(BookingStatus, name="booking_status"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bookings"),
    )
    op.create_index("ix_bookings_email", "bookings", ["email"])
    op.create_index("ix_bookings_booking_date", "bookings", ["booking_date"])
    op.create_index("ix_bookings_status", "bookings", ["status"])

    op.create_table(
        "contact_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_contact_messages"),
    )
    op.create_index("ix_contact_messages_email", "contact_messages", ["email"])


def downgrade() -> None:
    op.drop_table("contact_messages")
    op.drop_table("bookings")
    op.drop_table("inquiries")
    op.drop_table("gallery_images")
    op.drop_table("portfolios")
    op.drop_table("admin_users")

    # Drop enums
    bind = op.get_bind()
    for enum_name in ("package_interest", "booking_status", "inquiry_status", "portfolio_category"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
