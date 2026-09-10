"""Operator commands cannot silently reset accounts or create default credentials."""

from __future__ import annotations

import copy
import io
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app import cli
from app.core.security import verify_password
from app.db import session as db
from app.db.seed import _DEMO_PORTFOLIOS, seed_portfolios
from app.models import AdminUser, GalleryImage, Portfolio
from app.schemas.auth import AdminCreate
from tests.test_platform import migrated_engine  # noqa: F401


async def test_admin_creation_and_repeat_never_resets_existing_account(migrated_engine):
    factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    payload = AdminCreate(email="OPERATOR@example.com", password="Real-password-42", full_name="Operator")
    async with factory() as session:
        assert await cli.create_admin_account(session, payload)
        account = await session.scalar(select(AdminUser))
        assert account.email == "operator@example.com"
        assert account.is_active and account.is_superuser
        assert verify_password("Real-password-42", account.hashed_password)
        old_hash = account.hashed_password
        account.is_active = False
        account.is_superuser = False
        await session.commit()
        assert not await cli.create_admin_account(
            session, AdminCreate(email="operator@example.com", password="Another-password-42", full_name="Changed")
        )
        await session.refresh(account)
        assert account.hashed_password == old_hash
        assert account.full_name == "Operator"
        assert not account.is_active and not account.is_superuser
        assert await session.scalar(select(func.count()).select_from(AdminUser)) == 1


async def test_demo_seed_is_repeatable_without_mutating_source_or_creating_admins(migrated_engine):
    factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    source = copy.deepcopy(_DEMO_PORTFOLIOS)
    async with factory() as session:
        await seed_portfolios(session)
        await seed_portfolios(session)
        assert await session.scalar(select(func.count()).select_from(Portfolio)) == len(source)
        assert await session.scalar(select(func.count()).select_from(AdminUser)) == 0
        assert await session.scalar(select(func.count()).select_from(GalleryImage)) == sum(len(p["images"]) for p in source)
        assert _DEMO_PORTFOLIOS == source
        # A second empty database is represented by deleting only this isolated fixture's data.
        from sqlalchemy import delete

        await session.execute(delete(GalleryImage))
        await session.execute(delete(Portfolio))
        await session.commit()
        await seed_portfolios(session)
        assert _DEMO_PORTFOLIOS == source
        assert await session.scalar(select(func.count()).select_from(Portfolio)) == len(source)


async def test_cli_dispatch_validates_schema_and_disposes(migrated_engine, monkeypatch):
    dispose = AsyncMock()
    monkeypatch.setattr(db, "engine", SimpleNamespace(connect=migrated_engine.connect, dispose=dispose))
    monkeypatch.setattr(db, "SessionFactory", async_sessionmaker(migrated_engine, expire_on_commit=False))
    payload = AdminCreate(email="operator@example.com", password="Real-password-42")
    assert await cli._run("create-admin", payload) == "Administrator created."
    assert await cli._run("create-admin", payload) == "Account already exists; no changes made."
    assert dispose.await_count == 2


async def test_cli_dispatch_failure_disposes_without_seeding(monkeypatch):
    def unavailable():
        raise RuntimeError("secret database password")

    dispose = AsyncMock()
    factory = AsyncMock()
    monkeypatch.setattr(db, "engine", SimpleNamespace(connect=unavailable, dispose=dispose))
    monkeypatch.setattr(db, "SessionFactory", factory)
    with pytest.raises(Exception, match="alembic upgrade head") as failure:
        await cli._run("seed-demo", None)
    assert "secret database password" not in str(failure.value)
    factory.assert_not_called()
    dispose.assert_awaited_once()


def test_password_stdin_and_main_success(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("Real-password-42\n"))
    runner = AsyncMock(return_value="Administrator created.")
    monkeypatch.setattr(cli, "_run", runner)
    assert cli.main(["create-admin", "--email", "operator@example.com", "--password-stdin"]) == 0
    payload = runner.await_args.args[1]
    assert payload.password == "Real-password-42"
    assert payload.is_superuser
    output = capsys.readouterr()
    assert "Administrator created." in output.out
    assert "Real-password" not in output.out + output.err


def test_hidden_password_prompt(monkeypatch):
    monkeypatch.setattr("sys.stdin", SimpleNamespace(isatty=lambda: True))
    passwords = iter(["Real-password-42", "Real-password-42"])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: next(passwords))
    payload = cli._read_admin(cli._parser().parse_args(["create-admin", "--email", "operator@example.com"]))
    assert payload.password == "Real-password-42"


@pytest.mark.parametrize("password", ["", "short", " " * 12, "x" * 73, "é" * 37])
def test_invalid_passwords_exit_nonzero_without_echoing_input(password, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(password + "\n"))
    runner = AsyncMock()
    monkeypatch.setattr(cli, "_run", runner)
    assert cli.main(["create-admin", "--email", "operator@example.com", "--password-stdin"]) == 1
    runner.assert_not_called()
    assert "Traceback" not in capsys.readouterr().err


def test_bad_email_and_noninteractive_prompt_fail(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("Real-password-42\n"))
    assert cli.main(["create-admin", "--email", "bad-email", "--password-stdin"]) == 1
    assert cli.main(["create-admin", "--email", "operator@example.com"]) == 1


def test_password_argument_is_rejected_without_echo(monkeypatch, capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["create-admin", "--email", "operator@example.com", "--password", "never-echo-this"])
    assert error.value.code == 2
    assert "never-echo-this" not in capsys.readouterr().err


def test_command_failure_is_nonzero_and_redacted(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_run", AsyncMock(side_effect=RuntimeError("secret-from-database")))
    assert cli.main(["seed-demo"]) == 1
    output = capsys.readouterr()
    assert "alembic upgrade head" in output.err
    assert "secret-from-database" not in output.err


def test_real_module_refuses_unmigrated_database_without_creating_files():
    environment = {
        **os.environ,
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "SECRET_KEY": "isolated-cli-test-signing-secret-32-characters",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = subprocess.run(
        [
            sys.executable, "-m", "app.cli", "create-admin",
            "--email", "operator@example.com", "--password-stdin",
        ],
        input="Do-not-print-this-password-42\n",
        text=True,
        capture_output=True,
        env=environment,
        cwd=Path(__file__).resolve().parents[1],
        timeout=15,
    )
    assert result.returncode == 1
    assert "alembic upgrade head" in result.stderr
    assert "Do-not-print" not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
