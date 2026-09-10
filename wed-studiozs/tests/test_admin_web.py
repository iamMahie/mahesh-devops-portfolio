"""Browser sessions, CSRF isolation, private pages and real admin API workflows."""

from __future__ import annotations

import re
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.api.deps import ADMIN_COOKIE, browser_csrf
from app.core.config import settings
from app.core.security import create_access_token
from app.models.admin import AdminUser
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def form_csrf(html: str) -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', html)
    assert match is not None, html
    return match.group(1)


async def browser_login(client: AsyncClient, *, password: str = ADMIN_PASSWORD):
    page = await client.get("/admin/login")
    assert page.status_code == 200
    return await client.post(
        "/admin/login",
        data={"email": ADMIN_EMAIL, "password": password, "csrf": form_csrf(page.text)},
    )


async def browser_headers(client: AsyncClient) -> dict[str, str]:
    result = await browser_login(client)
    assert result.status_code == 303, result.text
    page = await client.get("/admin")
    assert page.status_code == 200, page.text
    return {"X-CSRF-Token": form_csrf(page.text)}


@pytest.mark.parametrize("path", ["/admin", "/admin/inquiries", "/admin/bookings", "/admin/messages", "/admin/portfolios"])
async def test_admin_pages_require_browser_auth(client: AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    assert response.headers["cache-control"] == "no-store"
    assert "Test Admin" not in response.text


async def test_browser_login_cookie_and_private_shell(client: AsyncClient, admin_user) -> None:
    response = await browser_login(client)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    cookie = next(value for value in response.headers.get_list("set-cookie") if value.startswith(ADMIN_COOKIE))
    assert "HttpOnly" in cookie
    assert "Path=/" in cookie
    assert "SameSite=lax" in cookie
    assert "Max-Age=" in cookie
    assert "Secure" not in cookie
    token = client.cookies[ADMIN_COOKIE]
    for path in ["/admin", "/admin/inquiries", "/admin/bookings", "/admin/messages", "/admin/portfolios"]:
        page = await client.get(path)
        assert page.status_code == 200, page.text
        assert page.headers["cache-control"] == "no-store"
        assert "Test Admin" in page.text
        assert token not in page.text
        assert "localStorage" not in page.text
        assert "admin.js" in page.text
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL
    assert me.headers["cache-control"] == "no-store"


async def test_browser_login_uses_secure_cookie_in_production(client: AsyncClient, admin_user, monkeypatch) -> None:
    page = await client.get("/admin/login")
    monkeypatch.setattr(settings, "environment", "production")
    response = await client.post("/admin/login", data={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "csrf": form_csrf(page.text),
    })
    assert response.status_code == 303
    cookie = next(value for value in response.headers.get_list("set-cookie") if value.startswith(ADMIN_COOKIE))
    assert "Secure" in cookie
    assert "HttpOnly" in cookie


async def test_login_validates_csrf_and_does_not_preserve_password(client: AsyncClient, admin_user) -> None:
    response = await client.post("/admin/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 403
    assert ADMIN_COOKIE not in client.cookies
    assert ADMIN_PASSWORD not in response.text
    assert f'value="{ADMIN_EMAIL}"' in response.text
    page = await client.get("/admin/login")
    invalid = await client.post("/admin/login", data={
        "email": "not-an-email", "password": "short", "csrf": form_csrf(page.text),
    })
    assert invalid.status_code == 422
    assert 'value="not-an-email"' in invalid.text
    assert 'value="short"' not in invalid.text
    failure = await browser_login(client, password="NotThePassword99")
    assert failure.status_code == 401
    assert "Incorrect email or password" in failure.text
    assert "NotThePassword99" not in failure.text


async def test_login_rejects_forged_form_and_has_fixed_destination(client: AsyncClient, admin_user) -> None:
    page = await client.get("/admin/login")
    bad = await client.post("/admin/login", data={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "csrf": "forged",
    })
    assert bad.status_code == 403
    result = await client.post("/admin/login?next=https://example.org", data={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "csrf": form_csrf(bad.text),
        "next": "https://example.org",
    })
    assert result.status_code == 303
    assert result.headers["location"] == "/admin"
    assert (await client.get("/admin/login")).headers["location"] == "/admin"


@pytest.mark.parametrize(("method", "path", "payload"), [
    ("POST", "/api/v1/portfolios", {"title": "Real collection", "category": "weddings"}),
    ("PATCH", "/api/v1/portfolios/1", {"is_featured": True}),
    ("DELETE", "/api/v1/portfolios/1", None),
    ("POST", "/api/v1/portfolios/1/images", {"portfolio_id": 1, "image_url": "/static/img/photo.jpg"}),
    ("PATCH", "/api/v1/images/1", {"title": "Updated caption"}),
    ("DELETE", "/api/v1/images/1", None),
    ("PUT", "/api/v1/portfolios/1/images/reorder", {"items": [{"id": 1, "display_order": 1}]}),
    ("PUT", "/api/v1/portfolios/1/images/1/feature", None),
    ("PATCH", "/api/v1/inquiries/1/status", {"status": "contacted"}),
    ("DELETE", "/api/v1/inquiries/1", None),
    ("PATCH", "/api/v1/bookings/1/status", {"status": "confirmed"}),
    ("DELETE", "/api/v1/bookings/1", None),
    ("PATCH", "/api/v1/contact/messages/1/read", None),
    ("DELETE", "/api/v1/contact/messages/1", None),
    ("POST", "/api/v1/auth/admins", {"email": "other@example.com", "password": "Admin@12345"}),
])
async def test_every_cookie_authenticated_write_requires_csrf(
    client: AsyncClient, admin_user, method: str, path: str, payload: dict | None,
) -> None:
    await browser_login(client)
    response = await client.request(method, path, json=payload)
    assert response.status_code == 403, response.text
    forged = await client.request(method, path, json=payload, headers={"X-CSRF-Token": "forged"})
    assert forged.status_code == 403, forged.text


async def test_csrf_is_bound_to_independent_browser_session(client: AsyncClient, admin_user) -> None:
    headers = await browser_headers(client)
    old_token = client.cookies[ADMIN_COOKIE]
    client.cookies.clear()
    current_headers = await browser_headers(client)
    assert client.cookies[ADMIN_COOKIE] != old_token
    assert current_headers != headers
    result = await client.post("/api/v1/portfolios", json={
        "title": "A real wedding", "category": "weddings",
    }, headers=headers)
    assert result.status_code == 403
    assert (await client.get("/api/v1/portfolios")).json()["total"] == 0


async def test_bearer_contract_has_precedence_and_needs_no_csrf(client: AsyncClient, admin_user, auth_headers) -> None:
    await browser_login(client)
    result = await client.post("/api/v1/portfolios", json={
        "title": "API collection", "category": "events",
    }, headers=auth_headers)
    assert result.status_code == 201
    for authorization in ["Bearer invalid", "Basic invalid", "Bearer", ""]:
        response = await client.get("/api/v1/auth/me", headers={"Authorization": authorization})
        assert response.status_code == 401
    client.cookies.clear()
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200


async def test_logout_requires_csrf_then_clears_session(client: AsyncClient, admin_user) -> None:
    headers = await browser_headers(client)
    missing = await client.post("/admin/logout")
    assert missing.status_code == 403
    assert (await client.get("/api/v1/auth/me")).status_code == 200
    forged = await client.post("/admin/logout", data={"csrf": "forged"})
    assert forged.status_code == 403
    response = await client.post("/admin/logout", data={"csrf": headers["X-CSRF-Token"]})
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    assert ADMIN_COOKIE not in client.cookies
    assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.parametrize("cookie", ["invalid", "expired"])
async def test_invalid_session_redirects_pages_and_rejects_api(client: AsyncClient, admin_user, cookie: str) -> None:
    value = create_access_token(ADMIN_EMAIL, expires_minutes=-1)[0] if cookie == "expired" else cookie
    client.cookies.set(ADMIN_COOKIE, value)
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    response = await client.post("/api/v1/portfolios", json={"title": "No access", "category": "weddings"})
    assert response.status_code == 401
    page = await client.get("/admin")
    assert page.status_code == 303
    assert page.headers["location"] == "/admin/login"


async def test_disabled_cookie_account_is_401_but_bearer_remains_403(client: AsyncClient, admin_user, auth_headers, db_session) -> None:
    await browser_login(client)
    account = await db_session.get(AdminUser, admin_user.id)
    account.is_active = False
    await db_session.commit()
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (await client.get("/api/v1/auth/me", headers=auth_headers)).status_code == 403
    assert (await client.get("/admin")).status_code == 303


async def test_cookie_portfolio_and_gallery_workflow(client: AsyncClient, admin_user) -> None:
    headers = await browser_headers(client)
    created = await client.post("/api/v1/portfolios", headers=headers, json={
        "title": "The Wedding Journal", "category": "weddings", "description": "Real studio work.",
    })
    assert created.status_code == 201, created.text
    portfolio = created.json()
    portfolio_id = portfolio["id"]
    updated = await client.patch(f"/api/v1/portfolios/{portfolio_id}", headers=headers, json={
        "title": "Our Wedding Journal", "slug": portfolio["slug"], "is_featured": True,
    })
    assert updated.status_code == 200
    assert updated.json()["is_featured"] is True
    image = await client.post(f"/api/v1/portfolios/{portfolio_id}/images", headers=headers, json={
        "portfolio_id": portfolio_id, "image_url": "/static/img/wedding.jpg", "title": "Ceremony", "display_order": 1,
    })
    assert image.status_code == 201
    image_id = image.json()["id"]
    assert (await client.patch(f"/api/v1/images/{image_id}", headers=headers, json={"title": "The ceremony", "display_order": 2})).status_code == 200
    assert (await client.put(f"/api/v1/portfolios/{portfolio_id}/images/{image_id}/feature", headers=headers)).status_code == 200
    published = (await client.get(f"/api/v1/portfolios/{portfolio_id}")).json()
    assert published["cover_image_url"] == "/static/img/wedding.jpg"
    assert published["images"][0]["title"] == "The ceremony"
    assert (await client.get("/api/v1/portfolios?search=Journal&is_featured=true&size=1")).json()["total"] == 1
    assert (await client.delete(f"/api/v1/images/{image_id}", headers=headers)).status_code == 204
    assert (await client.delete(f"/api/v1/portfolios/{portfolio_id}", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/portfolios")).json()["total"] == 0


async def test_cookie_customer_workflows_and_real_counts(client: AsyncClient, admin_user) -> None:
    headers = await browser_headers(client)
    inquiry = (await client.post("/api/v1/inquiries", json={
        "customer_name": "Wedding Customer", "email": "customer@example.com", "message": "A real enquiry",
    })).json()
    booking = (await client.post("/api/v1/bookings", json={
        "customer_name": "Consultation Customer", "email": "customer@example.com",
        "booking_date": (date.today() + timedelta(days=2)).isoformat(),
    })).json()
    message = (await client.post("/api/v1/contact/messages", json={
        "name": "Message Customer", "email": "customer@example.com", "subject": "Wedding details",
        "message": "<script>alert('not executable')</script>",
    })).json()
    for path in ["/inquiries?status=new", "/bookings?status=pending", "/contact/messages?is_read=false"]:
        result = await client.get(f"/api/v1{path}&size=1")
        assert result.status_code == 200
        assert result.json()["total"] == 1
    for status in ["contacted", "quoted", "won"]:
        result = await client.patch(f"/api/v1/inquiries/{inquiry['id']}/status", headers=headers, json={"status": status})
        assert result.status_code == 200
        assert result.json()["status"] == status
    terminal = await client.patch(f"/api/v1/inquiries/{inquiry['id']}/status", headers=headers, json={"status": "new"})
    assert terminal.status_code == 409
    for status in ["confirmed", "completed"]:
        result = await client.patch(f"/api/v1/bookings/{booking['id']}/status", headers=headers, json={"status": status})
        assert result.status_code == 200
    result = await client.patch(f"/api/v1/contact/messages/{message['id']}/read", headers=headers)
    assert result.json()["is_read"] is True
    assert (await client.get("/api/v1/contact/messages?is_read=false")).json()["total"] == 0
    assert (await client.get("/api/v1/contact/messages?search=Customer")).json()["total"] == 1
    for path, record in [("/inquiries", inquiry), ("/bookings", booking), ("/contact/messages", message)]:
        assert (await client.delete(f"/api/v1{path}/{record['id']}", headers=headers)).status_code == 204


async def test_browser_assets_do_not_use_token_storage_or_html_injection(client: AsyncClient) -> None:
    script = await client.get("/static/js/admin.js")
    assert script.status_code == 200
    for unsafe in ["localStorage", "sessionStorage", "innerHTML", "insertAdjacentHTML"]:
        assert unsafe not in script.text
    assert "X-CSRF-Token" in script.text
    assert "textContent" in script.text
    assert 'window.location.assign("/admin/login")' in script.text


async def test_csrf_token_does_not_reveal_session_credential() -> None:
    token, _ = create_access_token(ADMIN_EMAIL)
    derived = browser_csrf(token)
    assert len(derived) == 64
    assert token not in derived
    assert browser_csrf(token, purpose="login") != derived


@pytest.mark.parametrize("csrf", ["é" * 64, "f" * 1000, "a" * 63])
async def test_malformed_login_csrf_is_rejected_without_server_error(client, csrf):
    await client.get("/admin/login")
    response = await client.post(
        "/admin/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "csrf": csrf},
    )
    assert response.status_code == 403
    assert ADMIN_COOKIE not in client.cookies
