"""Portfolio + gallery CRUD, pagination, search and filtering."""

from __future__ import annotations

from httpx import AsyncClient


async def _create_portfolio(client: AsyncClient, headers: dict[str, str], **overrides) -> dict:
    payload = {
        "title": "Aarav & Meera Wedding",
        "description": "Three days in Udaipur.",
        "category": "weddings",
        "cover_image_url": "https://example.com/cover.jpg",
        "is_featured": True,
        "images": [
            {"image_url": "https://example.com/1.jpg", "title": "Baraat", "display_order": 0},
            {"image_url": "https://example.com/2.jpg", "title": "Vows", "display_order": 1},
        ],
    } | overrides
    response = await client.post("/api/v1/portfolios", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_generates_slug_and_nested_images(client, auth_headers) -> None:
    data = await _create_portfolio(client, auth_headers)
    assert data["slug"] == "aarav-meera-wedding"
    assert len(data["images"]) == 2
    assert [img["display_order"] for img in data["images"]] == [0, 1]


async def test_duplicate_titles_get_unique_slugs(client, auth_headers) -> None:
    first = await _create_portfolio(client, auth_headers)
    second = await _create_portfolio(client, auth_headers)
    assert first["slug"] == "aarav-meera-wedding"
    assert second["slug"] == "aarav-meera-wedding-2"


async def test_get_by_slug_and_missing_returns_404(client, auth_headers) -> None:
    created = await _create_portfolio(client, auth_headers)

    ok = await client.get(f"/api/v1/portfolios/slug/{created['slug']}")
    assert ok.status_code == 200
    assert ok.json()["id"] == created["id"]

    missing = await client.get("/api/v1/portfolios/slug/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


async def test_list_is_paginated(client, auth_headers) -> None:
    for index in range(5):
        await _create_portfolio(client, auth_headers, title=f"Event Number {index}")

    response = await client.get("/api/v1/portfolios", params={"page": 1, "size": 2})
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 5
    assert page["pages"] == 3
    assert len(page["items"]) == 2


async def test_filter_by_category_and_search(client, auth_headers) -> None:
    await _create_portfolio(client, auth_headers, title="Beach Maternity", category="maternity")
    await _create_portfolio(client, auth_headers, title="Rooftop Engagement", category="engagements")

    by_category = await client.get("/api/v1/portfolios", params={"category": "maternity"})
    assert by_category.json()["total"] == 1

    by_search = await client.get("/api/v1/portfolios", params={"search": "rooftop"})
    assert by_search.json()["total"] == 1
    assert by_search.json()["items"][0]["title"] == "Rooftop Engagement"


async def test_featured_endpoint(client, auth_headers) -> None:
    await _create_portfolio(client, auth_headers, title="Featured One", is_featured=True)
    await _create_portfolio(client, auth_headers, title="Hidden One", is_featured=False)

    response = await client.get("/api/v1/portfolios/featured")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert "Featured One" in titles
    assert "Hidden One" not in titles


async def test_update_and_delete(client, auth_headers) -> None:
    created = await _create_portfolio(client, auth_headers)

    patched = await client.patch(
        f"/api/v1/portfolios/{created['id']}",
        json={"description": "Updated copy", "is_featured": False},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["description"] == "Updated copy"
    assert patched.json()["is_featured"] is False

    deleted = await client.delete(f"/api/v1/portfolios/{created['id']}", headers=auth_headers)
    assert deleted.status_code == 204
    assert (await client.get(f"/api/v1/portfolios/{created['id']}")).status_code == 404


async def test_gallery_add_reorder_and_feature(client, auth_headers) -> None:
    portfolio = await _create_portfolio(client, auth_headers)
    pid = portfolio["id"]

    added = await client.post(
        f"/api/v1/portfolios/{pid}/images",
        json={"portfolio_id": pid, "image_url": "https://example.com/3.jpg", "title": "Exit"},
        headers=auth_headers,
    )
    assert added.status_code == 201
    new_id = added.json()["id"]

    images = (await client.get(f"/api/v1/portfolios/{pid}/images")).json()
    assert len(images) == 3

    # Send the complete ordering so the result is unambiguous.
    existing_ids = [img["id"] for img in images if img["id"] != new_id]
    reordered = await client.put(
        f"/api/v1/portfolios/{pid}/images/reorder",
        json={
            "items": [{"id": new_id, "display_order": 0}]
            + [{"id": img_id, "display_order": i} for i, img_id in enumerate(existing_ids, 1)]
        },
        headers=auth_headers,
    )
    assert reordered.status_code == 200
    assert [img["id"] for img in reordered.json()] == [new_id, *existing_ids]

    featured = await client.put(
        f"/api/v1/portfolios/{pid}/images/{new_id}/feature", headers=auth_headers
    )
    assert featured.status_code == 200
    detail = (await client.get(f"/api/v1/portfolios/{pid}")).json()
    assert detail["cover_image_url"] == "https://example.com/3.jpg"


async def test_invalid_payload_returns_422(client, auth_headers) -> None:
    response = await client.post(
        "/api/v1/portfolios", json={"title": "no", "category": "weddings"}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
