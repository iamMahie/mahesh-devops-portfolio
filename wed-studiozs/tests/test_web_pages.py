"""Server-rendered page smoke tests."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_home_page_renders(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "WED STUDIOZS" in response.text


async def test_portfolio_list_page_renders(client: AsyncClient) -> None:
    response = await client.get("/portfolios")
    assert response.status_code == 200
    assert "Portfolio" in response.text


async def test_contact_form_submission(client: AsyncClient) -> None:
    response = await client.post(
        "/contact",
        data={
            "name": "Priya",
            "email": "priya@example.com",
            "subject": "Studio visit",
            "message": "Can we visit the studio this Saturday afternoon?",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Message sent" in response.text


async def test_inquiry_form_redirects_to_thanks(client: AsyncClient) -> None:
    response = await client.post(
        "/inquiry",
        data={"customer_name": "Ravi Kumar", "email": "ravi@example.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Thanks, Ravi Kumar" in response.text


@pytest.mark.parametrize("path", ["/inquiry", "/booking", "/contact"])
async def test_public_forms_have_labels_and_no_cdn_dependency(client, path):
    response = await client.get(path)
    assert response.status_code == 200
    assert 'for="email"' in response.text
    assert 'autocomplete="email"' in response.text
    assert "cdn.jsdelivr.net" not in response.text
    assert "novalidate" not in response.text


async def test_blank_category_and_optional_inquiry_fields(client):
    response = await client.get("/portfolios?category=&q=")
    assert response.status_code == 200
    response = await client.post(
        "/inquiry",
        data={
            "customer_name": "Ravi Kumar", "email": "ravi@example.com",
            "event_date": "", "package_interest": "", "phone": "", "location": "", "message": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Thanks, Ravi Kumar" in response.text


async def test_form_error_preserves_input_and_explains_fields(client):
    response = await client.post(
        "/inquiry",
        data={"customer_name": "Ravi Kumar", "email": "not-an-email", "event_date": "not-a-date"},
    )
    assert response.status_code == 422
    assert 'value="Ravi Kumar"' in response.text
    assert 'value="not-an-email"' in response.text
    assert 'id="email-error"' in response.text
    assert 'id="event_date-error"' in response.text
    assert 'aria-invalid="true"' in response.text
    assert "pydantic.dev" not in response.text


async def test_booking_uses_redirect_and_does_not_confirm_appointment(client):
    response = await client.post(
        "/booking",
        data={
            "customer_name": "Ravi Kumar", "email": "ravi@example.com",
            "booking_date": (date.today() + timedelta(days=1)).isoformat(), "notes": "",
        },
    )
    assert response.status_code == 303
    receipt = await client.get(response.headers["location"])
    assert receipt.status_code == 200
    assert "not a confirmed appointment" in receipt.text
    assert receipt.headers["cache-control"] == "no-store"


async def test_inquiry_receipt_is_private_and_bound_to_reference(client):
    response = await client.post(
        "/inquiry", data={"customer_name": "Ravi Kumar", "email": "ravi@example.com"},
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert (await client.get(location)).status_code == 200
    assert (await client.get("/inquiry/99999/thanks")).status_code == 404
    client.cookies.clear()
    unknown = await client.get(location)
    assert unknown.status_code == 404
    assert "Ravi Kumar" not in unknown.text
    assert "ravi@example.com" not in unknown.text


async def test_receipt_rejects_tampering(client):
    client.cookies.set("ws_receipt", "not.a.valid-token")
    response = await client.get("/contact/thanks")
    assert response.status_code == 404


async def test_instagram_journal_uses_real_local_assets(client):
    response = await client.get("/")
    assert "/static/img/DZPAihNH5lW.jpg" in response.text
    assert "images.unsplash.com" not in response.text
    assert "400+" not in response.text
    story = await client.get("/journal/swaroop-and-gayatri")
    assert story.status_code == 200
    assert "https://www.instagram.com/wed_studiozs/p/DbLMpWDHwcu/" in story.text
    image = await client.get("/static/img/DbLMpWDHwcu.jpg")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert (await client.get("/journal/not-a-story")).status_code == 404


async def test_instagram_journal_filters_by_search_and_category(client):
    response = await client.get("/portfolios?q=Sneha&category=weddings")
    assert response.status_code == 200
    assert "/journal/snehas-wedding" in response.text
    assert "/journal/temple-diaries" not in response.text
    response = await client.get("/portfolios?q=nothing-matches-this")
    assert "No stories found." in response.text


async def test_pagination_preserves_search_category_and_size(client, auth_headers):
    for index in range(3):
        response = await client.post(
            "/api/v1/portfolios", headers=auth_headers,
            json={"title": f"Searchable Wedding {index}", "category": "weddings"},
        )
        assert response.status_code == 201
    response = await client.get("/portfolios?q=Searchable&category=weddings&size=1")
    assert response.status_code == 200
    assert "q=Searchable&amp;category=weddings&amp;size=1&amp;page=2" in response.text
    assert "page=0" not in response.text


async def test_public_form_input_is_escaped(client):
    response = await client.post(
        "/contact",
        data={
            "name": '<script>alert("x")</script>', "email": "bad-email",
            "subject": "Question", "message": "A valid message for the studio.",
        },
    )
    assert response.status_code == 422
    assert '<script>alert("x")</script>' not in response.text
    assert "&lt;script&gt;" in response.text
