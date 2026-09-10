"""Publishing controls must not store executable image links or invalid updates."""

import pytest


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "data:text/html,hello", "//other.example/image.jpg",
    "/static/../admin", "https://example.com\\@other.example/x",
    "https://name:password@example.com/image.jpg",
])
async def test_reject_unsafe_cover_urls(client, auth_headers, url):
    response = await client.post(
        "/api/v1/portfolios", headers=auth_headers,
        json={"title": "A new story", "category": "weddings", "cover_image_url": url},
    )
    assert response.status_code == 422


async def test_publishing_accepts_studio_static_photographs(client, auth_headers):
    response = await client.post(
        "/api/v1/portfolios", headers=auth_headers,
        json={
            "title": "A studio collection", "category": "weddings",
            "cover_image_url": "/static/img/DWG0OP8khUz.jpg",
            "images": [{"image_url": "/static/img/DWG0OP8khUz.jpg"}],
        },
    )
    assert response.status_code == 201
    assert response.json()["images"][0]["image_url"] == "/static/img/DWG0OP8khUz.jpg"


@pytest.mark.parametrize("field", ["title", "slug", "category", "is_featured"])
async def test_null_required_portfolio_update_is_validation_error(client, auth_headers, field):
    response = await client.patch(
        "/api/v1/portfolios/1", headers=auth_headers, json={field: None},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("title", ["   ", "  a  ", " ab "])
async def test_title_length_is_checked_after_trimming(client, auth_headers, title):
    response = await client.post(
        "/api/v1/portfolios", headers=auth_headers,
        json={"title": title, "category": "weddings"},
    )
    assert response.status_code == 422


async def test_gallery_honours_explicit_zero_order(client, auth_headers):
    created = await client.post(
        "/api/v1/portfolios", headers=auth_headers,
        json={
            "title": "Ordered collection", "category": "weddings",
            "images": [
                {"image_url": "/static/img/DWG0OP8khUz.jpg", "display_order": 5},
                {"image_url": "/static/img/DbLMpWDHwcu.jpg", "display_order": 0},
            ],
        },
    )
    assert created.status_code == 201
    portfolio_id = created.json()["id"]
    assert created.json()["images"][1]["display_order"] == 0
    added = await client.post(
        f"/api/v1/portfolios/{portfolio_id}/images", headers=auth_headers,
        json={
            "portfolio_id": portfolio_id,
            "image_url": "/static/img/DZPAihNH5lW.jpg", "display_order": 0,
        },
    )
    assert added.status_code == 201
    assert added.json()["display_order"] == 0
    appended = await client.post(
        f"/api/v1/portfolios/{portfolio_id}/images", headers=auth_headers,
        json={"portfolio_id": portfolio_id, "image_url": "/static/img/DWD4g5WEfLX.jpg"},
    )
    assert appended.status_code == 201
    assert appended.json()["display_order"] > 5
