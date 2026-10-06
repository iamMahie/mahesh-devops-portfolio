"""Content editing, publication boundaries and migration coverage."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.models import Base
from tests.test_admin_web import browser_login, form_csrf


@pytest.fixture
async def editor(client, admin_user):
    assert (await browser_login(client)).status_code == 303
    page = await client.get("/admin/content")
    assert page.status_code == 200
    return form_csrf(page.text)


def film(csrf, **overrides):
    return {
        "csrf": csrf, "title": "A wedding film",
        "video_url": "https://media.example.com/wedding.mp4",
        "poster_url": "/static/img/DWD4g5WEfLX.jpg",
        "captions_url": "", "description": "A moment from the celebration.",
        "display_order": "0", "is_published": "on", **overrides,
    }


def details(csrf, **overrides):
    return {
        "csrf": csrf, "footer_text": "Photographs and films, made with care.",
        "phone": "+91 91604 00802", "email": "studio@example.com",
        "address": "Studio address supplied by the administrator",
        "instagram_handle": "wed_studiozs", **overrides,
    }


@pytest.mark.parametrize("method,path", [
    ("GET", "/admin/content"), ("POST", "/admin/content/details"),
    ("POST", "/admin/content/reels"), ("POST", "/admin/content/reels/1/delete"),
])
async def test_content_requires_sign_in(client, method, path):
    response = await client.request(method, path)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("path", [
    "/admin/content/details", "/admin/content/reels", "/admin/content/reels/1/delete",
])
async def test_all_content_writes_require_csrf(client, editor, path):
    response = await client.post(path, data=film("invalid"))
    assert response.status_code == 403
    assert "security check" in response.text


async def test_publish_edit_draft_and_delete_film(client, editor):
    saved = await client.post("/admin/content/reels", data=film(editor))
    assert saved.status_code == 303
    assert saved.headers["location"] == "/admin/content?saved=reel#films"
    for path in ["/", "/films"]:
        response = await client.get(path)
        assert "https://media.example.com/wedding.mp4" in response.text
        assert 'preload="none" muted loop playsinline controls' in response.text
        assert "data-sound" in response.text
        assert "autoplay" not in response.text
    edited = await client.post("/admin/content/reels?edit=1", data=film(
        editor, title="Updated title", is_published="", captions_url="/static/media/film.vtt",
    ))
    assert edited.status_code == 303
    assert "Updated title" not in (await client.get("/films")).text
    assert "Updated title" in (await client.get("/admin/content?edit=1")).text
    assert "wedding.mp4" not in (await client.get("/")).text
    response = await client.post(
        "/admin/content/reels/1/delete", data={"csrf": editor},
    )
    assert response.status_code == 422
    assert "Updated title" in (await client.get("/admin/content")).text
    response = await client.post(
        "/admin/content/reels/1/delete", data={"csrf": editor, "confirm": "yes"},
    )
    assert response.status_code == 303
    assert "Updated title" not in (await client.get("/admin/content")).text


@pytest.mark.parametrize("field,value", [
    ("video_url", "https://www.instagram.com/reel/123/"),
    ("video_url", "javascript:alert(1)"), ("video_url", "http://media.example.com/file.mp4"),
    ("video_url", "/static/../secret.mp4"), ("video_url", "//evil.example/video.mp4"),
    ("poster_url", "data:image/png,abc"), ("poster_url", ""),
    ("captions_url", "https://example.com/file.txt"),
    ("title", " "), ("display_order", "-1"), ("display_order", "100001"),
])
async def test_invalid_film_retains_values_without_saving(client, editor, field, value):
    response = await client.post(
        "/admin/content/reels", data=film(editor, **{field: value}),
    )
    assert response.status_code == 422
    assert 'aria-invalid="true"' in response.text
    assert "Nothing has been saved" in response.text
    assert "wedding.mp4" not in (await client.get("/films")).text


async def test_order_pagination_captions_and_empty_state(client, editor):
    for number in [4, 0, 2, 1]:
        assert (await client.post("/admin/content/reels", data=film(
            editor, title=f"Film {number}", display_order=str(number),
            captions_url="https://media.example.com/captions.vtt",
        ))).status_code == 303
    home = (await client.get("/")).text
    assert home.index("Film 0") < home.index("Film 1") < home.index("Film 2")
    assert "Film 4" not in home
    page = (await client.get("/films?size=2&page=2")).text
    assert "Film 0" not in page
    assert page.index("Film 2") < page.index("Film 4")
    assert 'kind="captions"' in page
    assert 'crossorigin="anonymous"' in page
    assert "size=2" in page
    assert "Return to the first page" in (await client.get("/films?page=20")).text


async def test_contact_details_are_shared_and_can_be_cleared(client, editor):
    assert (await client.post(
        "/admin/content/details", data=details(editor),
    )).status_code == 303
    for path in ["/", "/contact", "/portfolios", "/films", "/journal/temple-diaries"]:
        response = await client.get(path)
        assert "Photographs and films, made with care." in response.text
        assert "studio@example.com" in response.text
    api = (await client.get("/api/v1/contact/info")).json()
    assert api["email"] == "studio@example.com"
    assert api["phone"] == "+91 91604 00802"
    assert api["business_name"] == "WedStudiozs"
    await client.post("/admin/content/details", data=details(editor, email="", phone="", address=""))
    assert 'href="tel:' not in (await client.get("/contact")).text
    assert 'href="mailto:' not in (await client.get("/")).text
    assert (await client.get("/api/v1/contact/info")).json()["email"] == ""


@pytest.mark.parametrize("field,value", [
    ("email", "bad-address"), ("phone", "javascript:123"),
    ("instagram_handle", "../admin"), ("footer_text", " "),
])
async def test_invalid_details_do_not_save(client, editor, field, value):
    response = await client.post(
        "/admin/content/details", data=details(editor, **{field: value}),
    )
    assert response.status_code == 422
    assert "studio@example.com" != (await client.get("/api/v1/contact/info")).json()["email"]


async def test_content_is_escaped_and_unknown_edit_does_not_create(client, editor):
    await client.post("/admin/content/details", data=details(editor, footer_text="<script>alert(1)</script>"))
    home = (await client.get("/")).text
    assert "&lt;script&gt;" in home
    assert "<script>alert(1)</script>" not in home
    response = await client.post("/admin/content/reels?edit=999", data=film(editor))
    assert response.status_code == 404
    assert "wedding.mp4" not in (await client.get("/films")).text


async def test_migration_preserves_existing_records_and_matches_models():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))

    def migrate(connection):
        config.attributes["connection"] = connection
        command.upgrade(config, "0001")
        connection.execute(text(
            "INSERT INTO portfolios (id,title,slug,category,is_featured) "
            "VALUES (1,'Existing wedding','existing-wedding','weddings',0)"
        ))
        command.upgrade(config, "head")
        assert connection.scalar(text("SELECT title FROM portfolios WHERE id=1")) == "Existing wedding"
        assert {"site_content", "reels"}.issubset(inspect(connection).get_table_names())
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        command.downgrade(config, "0001")
        assert connection.scalar(text("SELECT title FROM portfolios WHERE id=1")) == "Existing wedding"
        assert "reels" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")

    try:
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
    finally:
        await engine.dispose()
