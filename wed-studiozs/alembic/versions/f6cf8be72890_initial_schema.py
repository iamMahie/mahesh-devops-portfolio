"""initial schema

Revision ID: f6cf8be72890
Revises: 
Create Date: 2026-09-11 22:09:50.776554
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'f6cf8be72890'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
