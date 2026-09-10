"""Database package.

Only metadata is re-exported here. Engine/session live in `app.db.session` and
are imported explicitly, so importing the ORM models (e.g. from Alembic, which
runs synchronously) never constructs an async engine.
"""

from app.db.base import Base, TimestampMixin

__all__ = ["Base", "TimestampMixin"]
