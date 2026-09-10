"""Test fixtures: in-memory SQLite, dependency overrides, auth helpers."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

# Configure the environment BEFORE importing anything that reads settings.
os.environ.update(
    ENVIRONMENT="testing",
    DEBUG="false",
    DATABASE_URL="sqlite+aiosqlite:///:memory:",
    SECRET_KEY="test-secret-key-for-unit-tests-only",
    FIRST_ADMIN_EMAIL="admin@example.com",
    FIRST_ADMIN_PASSWORD="Admin@12345",
)

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import AdminUser  # noqa: E402

# `.local` / `.test` are reserved domains that email-validator rejects.
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin@12345"


@pytest.fixture
async def engine():
    """One in-memory database shared by all connections for a single test."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest.fixture
async def admin_user(session_factory) -> AdminUser:
    async with session_factory() as session:
        admin = AdminUser(
            email=ADMIN_EMAIL,
            full_name="Test Admin",
            hashed_password=hash_password(ADMIN_PASSWORD),
            is_active=True,
            is_superuser=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin


@pytest.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    """ASGI client with the DB dependency pointed at the test database."""
    app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient, admin_user: AdminUser) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
