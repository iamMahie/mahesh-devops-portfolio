"""Inquiry, booking and contact flows including status-transition rules."""

from __future__ import annotations

from datetime import date, timedelta

from httpx import AsyncClient

TOMORROW = (date.today() + timedelta(days=1)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


async def _submit_inquiry(client: AsyncClient, **overrides) -> dict:
    payload = {
        "customer_name": "Ravi Kumar",
        "email": "ravi@example.com",
        "phone": "+91 98765 43210",
        "event_date": TOMORROW,
        "location": "Hyderabad",
        "package_interest": "signature",
        "message": "Looking for two-day wedding coverage.",
    } | overrides
    response = await client.post("/api/v1/inquiries", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_submit_inquiry_is_public_and_starts_as_new(client: AsyncClient) -> None:
    data = await _submit_inquiry(client)
    assert data["status"] == "new"
    assert data["email"] == "ravi@example.com"


async def test_past_event_date_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/inquiries",
        json={"customer_name": "Ravi", "email": "ravi@example.com", "event_date": YESTERDAY},
    )
    assert response.status_code == 422


async def test_listing_inquiries_requires_admin(client: AsyncClient) -> None:
    await _submit_inquiry(client)
    assert (await client.get("/api/v1/inquiries")).status_code == 401


async def test_inquiry_search_and_status_filter(client: AsyncClient, auth_headers) -> None:
    await _submit_inquiry(client, customer_name="Ravi Kumar", email="ravi@example.com")
    await _submit_inquiry(client, customer_name="Sneha Rao", email="sneha@example.com")

    all_items = await client.get("/api/v1/inquiries", headers=auth_headers)
    assert all_items.json()["total"] == 2

    searched = await client.get(
        "/api/v1/inquiries", params={"search": "sneha"}, headers=auth_headers
    )
    assert searched.json()["total"] == 1

    filtered = await client.get(
        "/api/v1/inquiries", params={"status": "won"}, headers=auth_headers
    )
    assert filtered.json()["total"] == 0


async def test_inquiry_status_transitions(client: AsyncClient, auth_headers) -> None:
    inquiry = await _submit_inquiry(client)
    url = f"/api/v1/inquiries/{inquiry['id']}/status"

    contacted = await client.patch(url, json={"status": "contacted"}, headers=auth_headers)
    assert contacted.json()["status"] == "contacted"

    # new -> won is not a legal jump from 'contacted'
    illegal = await client.patch(url, json={"status": "won"}, headers=auth_headers)
    assert illegal.status_code == 409
    assert illegal.json()["error"]["code"] == "conflict"

    assert (await client.patch(url, json={"status": "quoted"}, headers=auth_headers)).json()[
        "status"
    ] == "quoted"
    assert (await client.patch(url, json={"status": "won"}, headers=auth_headers)).json()[
        "status"
    ] == "won"


async def test_booking_flow_and_duplicate_guard(client: AsyncClient, auth_headers) -> None:
    payload = {
        "customer_name": "Ravi Kumar",
        "email": "ravi@example.com",
        "booking_date": TOMORROW,
        "notes": "Prefer an evening call.",
    }
    first = await client.post("/api/v1/bookings", json=payload)
    assert first.status_code == 201
    assert first.json()["status"] == "pending"

    duplicate = await client.post("/api/v1/bookings", json=payload)
    assert duplicate.status_code == 409

    confirmed = await client.patch(
        f"/api/v1/bookings/{first.json()['id']}/status",
        json={"status": "confirmed"},
        headers=auth_headers,
    )
    assert confirmed.json()["status"] == "confirmed"


async def test_booking_in_the_past_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/bookings",
        json={"customer_name": "Ravi", "email": "r@example.com", "booking_date": YESTERDAY},
    )
    assert response.status_code == 422


async def test_contact_message_flow(client: AsyncClient, auth_headers) -> None:
    created = await client.post(
        "/api/v1/contact/messages",
        json={
            "name": "Priya",
            "email": "priya@example.com",
            "subject": "Album pricing",
            "message": "Could you share the album upgrade pricing?",
        },
    )
    assert created.status_code == 201
    assert created.json()["is_read"] is False

    listed = await client.get("/api/v1/contact/messages", headers=auth_headers)
    assert listed.json()["total"] == 1

    read = await client.patch(
        f"/api/v1/contact/messages/{created.json()['id']}/read", headers=auth_headers
    )
    assert read.json()["is_read"] is True


async def test_contact_info_is_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/contact/info")
    assert response.status_code == 200
    assert "email" in response.json()
