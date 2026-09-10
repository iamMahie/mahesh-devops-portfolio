"""Read-only, bounded database compatibility checks shared by probes and the CLI."""

from __future__ import annotations

import asyncio

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models import Base


class DatabaseNotReady(RuntimeError):
    """A deliberately credential-free operational failure."""


MIGRATION_INSTRUCTIONS = (
    "Database schema is not compatible with this application. "
    "Run `alembic upgrade head` as a separate migration step before starting the app."
)


def _check_schema(connection: Connection) -> None:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if "alembic_version" not in tables or not set(Base.metadata.tables).issubset(tables):
        raise DatabaseNotReady(MIGRATION_INSTRUCTIONS)

    revisions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    if not revisions or any(not revision or not revision.strip() for revision in revisions):
        raise DatabaseNotReady(MIGRATION_INSTRUCTIONS)

    # Alembic stores current heads, not an applied-history ledger. A nonempty
    # migration stamp plus the full base contract permits newer rolling-release
    # revisions; exact-head equality would reject safe additive migrations.
    for table in Base.metadata.sorted_tables:
        actual_columns = {column["name"]: column for column in inspector.get_columns(table.name)}
        required_columns = set(table.columns.keys())
        if not required_columns.issubset(actual_columns):
            raise DatabaseNotReady(MIGRATION_INSTRUCTIONS)
        for name in actual_columns.keys() - required_columns:
            column = actual_columns[name]
            if not column["nullable"] and column.get("default") is None:
                raise DatabaseNotReady(MIGRATION_INSTRUCTIONS)
        # Also check read privileges and queryability without fetching user data.
        connection.execute(select(*table.columns).limit(0))


async def check_database(engine: AsyncEngine, timeout_seconds: float) -> None:
    try:
        async with asyncio.timeout(timeout_seconds):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                await connection.run_sync(_check_schema)
    except DatabaseNotReady:
        raise
    except Exception:
        raise DatabaseNotReady(
            "Database readiness check failed. Check database connectivity, permissions, "
            "and migration completion (`alembic upgrade head`)."
        ) from None
