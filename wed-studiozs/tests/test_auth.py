"""Authentication and route-protection tests."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD


async def test_login_returns_jwt(client: AsyncClient, admin_user) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["access_token"].count(".") == 2


async def test_login_with_wrong_password_is_401(client: AsyncClient, admin_user) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "WrongPassword1"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


async def test_me_requires_token(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_me_returns_admin(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == ADMIN_EMAIL


async def test_invalid_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


async def test_creating_portfolio_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/portfolios", json={"title": "Unauthorised", "category": "weddings"}
    )
    assert response.status_code == 401
