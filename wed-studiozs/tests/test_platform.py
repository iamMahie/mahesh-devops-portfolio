"""Deployment contract tests; migrations run against isolated in-memory databases."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.lifecycle import DatabaseNotReady, check_database
from app.core.observability import JsonFormatter, request_id_context, route_context
from app.main import create_app


@pytest.fixture
async def migrated_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)

    def migrate(connection):
        config = Config()
        config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    try:
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    "secret",
    [
        "",
        " " * 40,
        "short-key",
        "insecure-dev-key-change-me",
        "change-me-in-production-please-use-a-long-random-string",
    ],
)
def test_unsafe_signing_keys_are_rejected(secret):
    with pytest.raises(ValidationError) as failure:
        Settings(_env_file=None, secret_key=secret)
    assert "SECRET_KEY must" in str(failure.value)
    assert "input_value" not in str(failure.value)


def test_signing_key_is_required_and_debug_defaults_false(monkeypatch):
    monkeypatch.delenv("SECRET_KEY")
    monkeypatch.delenv("DEBUG")
    with pytest.raises(ValidationError, match="secret_key"):
        Settings(_env_file=None)
    config = Settings(_env_file=None, secret_key="a-generated-test-key-with-32-characters")
    assert config.debug is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("db_pool_size", 0),
        ("db_pool_size", 51),
        ("db_max_overflow", -1),
        ("db_max_overflow", 21),
        ("db_pool_timeout_seconds", 0),
        ("db_pool_recycle_seconds", 0),
        ("schema_check_timeout_seconds", 31),
        ("database_port", 65536),
    ],
)
def test_pool_and_timeout_settings_are_bounded(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})


def test_database_components_preserve_reserved_password_characters():
    password = "abc@:/#?% space"
    config = Settings(
        _env_file=None,
        database_url=None,
        database_user="operator",
        database_password=password,
        database_host="postgres",
    )
    assert make_url(config.database_url).password == password
    assert make_url(config.sync_database_url).password == password
    assert make_url(config.sync_database_url).drivername == "postgresql+psycopg2"
    assert password not in repr(config)


def test_database_url_precedence_normalization_and_redacted_errors():
    original = "postgresql://operator:encoded%40password@postgres:5432/studio"
    config = Settings(_env_file=None, database_url=original, database_password="ignored")
    assert make_url(config.database_url).password == "encoded@password"
    assert make_url(config.database_url).drivername == "postgresql+asyncpg"
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url="not-a-url-with-sensitive-data")
    assert "not-a-url-with-sensitive-data" not in str(error.value)


async def test_migrated_lifespan_readiness_and_cleanup(migrated_engine):
    app = create_app()
    dispose = AsyncMock(wraps=migrated_engine.dispose)
    app.state.db_engine = SimpleNamespace(connect=migrated_engine.connect, dispose=dispose)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/healthz")).status_code == 200
            assert (await client.get("/readyz")).json() == {"status": "ready"}
    dispose.assert_awaited_once()
    async with migrated_engine.connect() as connection:
        assert await connection.run_sync(lambda conn: inspect(conn).get_table_names()) == []


async def test_empty_schema_refuses_startup_without_creating_tables():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    app = create_app()
    dispose = AsyncMock(wraps=engine.dispose)
    app.state.db_engine = SimpleNamespace(connect=engine.connect, dispose=dispose)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/readyz")).status_code == 503
            assert (await client.get("/healthz")).status_code == 200
        with pytest.raises(DatabaseNotReady, match="alembic upgrade head"):
            async with app.router.lifespan_context(app):
                pytest.fail("Startup must fail")
        dispose.assert_awaited_once()
        async with engine.connect() as connection:
            assert await connection.run_sync(lambda conn: inspect(conn).get_table_names()) == []
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    "statement",
    [
        "DROP TABLE contact_messages",
        "ALTER TABLE portfolios DROP COLUMN description",
        "DROP TABLE alembic_version",
        "DELETE FROM alembic_version",
        "UPDATE alembic_version SET version_num = ' '",
        "ALTER TABLE portfolios ADD COLUMN incompatible_required_column TEXT NOT NULL",
    ],
)
async def test_missing_schema_contract_is_unready(migrated_engine, statement):
    async with migrated_engine.begin() as connection:
        await connection.execute(text(statement))
    with pytest.raises(DatabaseNotReady, match="alembic upgrade head"):
        await check_database(migrated_engine, 3)


async def test_forward_compatible_migration_is_accepted(migrated_engine):
    async with migrated_engine.begin() as connection:
        await connection.execute(text("ALTER TABLE portfolios ADD COLUMN future_caption TEXT"))
        await connection.execute(text("ALTER TABLE portfolios ADD COLUMN future_flag BOOLEAN NOT NULL DEFAULT false"))
        await connection.execute(text("UPDATE alembic_version SET version_num = 'future_expand_revision'"))
    await check_database(migrated_engine, 3)


async def test_outage_is_redacted_and_liveness_remains_independent(caplog):
    def unavailable():
        raise RuntimeError("postgresql://secret-user:secret-password@private-host/db")

    app = create_app()
    app.state.db_engine = SimpleNamespace(connect=unavailable, dispose=AsyncMock())
    with caplog.at_level(logging.INFO):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            ready = await client.get("/readyz")
            assert ready.status_code == 503
            assert ready.json() == {"status": "unavailable"}
            assert (await client.get("/healthz")).status_code == 200
        with pytest.raises(DatabaseNotReady) as failure:
            async with app.router.lifespan_context(app):
                pytest.fail("Startup must fail")
    assert "secret-password" not in str(failure.value)
    assert "secret-password" not in caplog.text
    app.state.db_engine.dispose.assert_awaited_once()


async def test_check_timeout_cancels_and_releases_connection():
    released = asyncio.Event()

    @asynccontextmanager
    async def connect():
        try:
            yield SimpleNamespace(execute=slow_query)
        finally:
            released.set()

    async def slow_query(*args):
        await asyncio.sleep(10)

    with pytest.raises(DatabaseNotReady, match="readiness check failed"):
        await asyncio.wait_for(check_database(SimpleNamespace(connect=connect), 0.02), timeout=0.5)
    assert released.is_set()


async def test_cleanup_after_application_error(migrated_engine):
    app = create_app()
    dispose = AsyncMock(wraps=migrated_engine.dispose)
    app.state.db_engine = SimpleNamespace(connect=migrated_engine.connect, dispose=dispose)
    with pytest.raises(RuntimeError, match="shutdown test"):
        async with app.router.lifespan_context(app):
            raise RuntimeError("shutdown test")
    dispose.assert_awaited_once()


async def test_request_ids_metrics_and_unhandled_errors(caplog):
    app = create_app()

    @app.get("/platform-items/{item_id}")
    async def item(item_id: str):
        return {"request_id": request_id_context.get()}

    @app.get("/platform-boom")
    async def boom():
        raise RuntimeError("sensitive exception content")

    with caplog.at_level(logging.INFO):
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
        ) as client:
            first, second = await asyncio.gather(
                client.get("/platform-items/private-a?token=secret-query", headers={"X-Request-ID": "req-one"}),
                client.get("/platform-items/private-b", headers={"X-Request-ID": "req-two"}),
            )
            assert first.headers["x-request-id"] == first.json()["request_id"] == "req-one"
            assert second.headers["x-request-id"] == second.json()["request_id"] == "req-two"
            invalid = await client.get("/healthz", headers={"X-Request-ID": "bad id\t"})
            assert len(invalid.headers["x-request-id"]) == 32
            duplicate = await client.get("/healthz", headers=[("X-Request-ID", "one"), ("X-Request-ID", "two")])
            assert duplicate.headers["x-request-id"] not in {"one", "two"}
            failed = await client.get("/platform-boom", headers={"X-Request-ID": "failed-request"})
            assert failed.status_code == 500
            assert failed.headers["x-request-id"] == "failed-request"
            assert "sensitive" not in failed.text
            await client.get("/private-unknown-path?token=secret-query")
            await client.get("/static/no-such-one.png")
            await client.get("/static/no-such-two.png")
            metrics = await client.get("/metrics")
    assert request_id_context.get() is None
    assert route_context.get() is None
    assert metrics.headers["content-type"].startswith("text/plain")
    assert 'route="/platform-items/{item_id}",status="200"} 2.0' in metrics.text
    assert 'route="/platform-boom",status="500"} 1.0' in metrics.text
    assert 'route="unmatched",status="404"} 1.0' in metrics.text
    assert 'route="/static/{path:path}",status="404"} 2.0' in metrics.text
    assert "wed_http_request_duration_seconds_count" in metrics.text
    for sensitive in ("private-a", "private-b", "secret-query", "private-unknown-path", "req-one"):
        assert sensitive not in metrics.text
    assert "secret-query" not in caplog.text


async def test_multiple_apps_have_independent_metric_registries():
    first, second = create_app(), create_app()
    async with AsyncClient(transport=ASGITransport(app=first), base_url="http://test") as client:
        await client.get("/healthz")
    assert first.state.metrics.registry is not second.state.metrics.registry
    async with AsyncClient(transport=ASGITransport(app=second), base_url="http://test") as client:
        assert 'route="/healthz"' not in (await client.get("/metrics")).text


def test_json_formatter_redacts_secrets_access_paths_and_exception_values():
    formatter = JsonFormatter(("configured-secret",))
    token = request_id_context.set("correlation-id")
    route_token = route_context.set("/portfolios/{slug}")
    try:
        access = logging.LogRecord(
            "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
            ("client", "GET", "/portfolios/private-name?token=secret", "1.1", 200), None,
        )
        formatted = json.loads(formatter.format(access))
        assert formatted["request_id"] == "correlation-id"
        assert formatted["route"] == "/portfolios/{slug}"
        assert formatted["message"] == "HTTP request"
        assert "private-name" not in json.dumps(formatted)
        try:
            raise RuntimeError("exception-secret")
        except RuntimeError:
            failure = logging.LogRecord(
                "uvicorn.error", logging.ERROR, "", 0, "Failure configured-secret", (), sys.exc_info()
            )
        output = formatter.format(failure)
        assert "configured-secret" not in output
        assert "exception-secret" not in output
        assert json.loads(output)["exception_type"] == "RuntimeError"
    finally:
        request_id_context.reset(token)
        route_context.reset(route_token)
    background = logging.LogRecord("uvicorn.error", logging.INFO, "", 0, "Startup", (), None)
    assert json.loads(formatter.format(background))["request_id"] is None


def test_uvicorn_and_application_loggers_emit_json_without_raw_access_urls():
    script = """
import logging
import app.main
logging.getLogger('wed_studiozs').info('Application event')
logging.getLogger('uvicorn.error').info('Server event')
logging.getLogger('uvicorn.access').info(
    '%s - "%s %s HTTP/%s" %d', 'client', 'GET', '/private?token=private-token', '1.1', 200
)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
            "SECRET_KEY": "isolated-log-test-signing-secret-32-characters",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        cwd=Path(__file__).resolve().parents[1],
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(events) == 3
    assert {event["logger"] for event in events} == {"wed_studiozs", "uvicorn.error", "uvicorn.access"}
    assert all(event["request_id"] is None for event in events)
    assert "private-token" not in result.stdout


def test_alembic_offline_accepts_percent_encoded_database_password(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "database_url", "postgresql+asyncpg://operator:p%40ss%25word@localhost/studio")
    output = io.StringIO()
    config = Config(output_buffer=output)
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    command.upgrade(config, "head", sql=True)
    assert "CREATE TABLE admin_users" in output.getvalue()
