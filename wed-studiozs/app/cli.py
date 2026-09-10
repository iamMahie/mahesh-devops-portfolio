"""Explicit, operator-run account bootstrap and optional demonstration data."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
import warnings

from pydantic import ValidationError

from app.schemas.auth import AdminCreate


class CommandError(Exception):
    pass


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # argparse normally repeats rejected argv, which may contain a password.
        self.print_usage(sys.stderr)
        self.exit(2, "Invalid arguments. Use --help; never pass a password as an argument.\n")


def _parser() -> argparse.ArgumentParser:
    parser = SafeArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser(
        "create-admin",
        help="Create an administrator without changing existing accounts.",
        allow_abbrev=False,
    )
    admin.add_argument("--email", required=True)
    admin.add_argument("--full-name", default="WED STUDIOZS Admin")
    admin.add_argument("--password-stdin", action="store_true", help="Read one password line from standard input.")
    commands.add_parser("seed-demo", help="Seed sample portfolios only, into an empty portfolio collection.")
    return parser


def _read_admin(args: argparse.Namespace) -> AdminCreate:
    if args.password_stdin:
        password = sys.stdin.readline(1025).rstrip("\r\n")
    else:
        if not sys.stdin.isatty():
            raise CommandError("A terminal is required for hidden input; otherwise use --password-stdin.")
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            try:
                password = getpass.getpass("Admin password: ")
                confirmation = getpass.getpass("Confirm password: ")
            except getpass.GetPassWarning:
                raise CommandError("Hidden password input is unavailable; use --password-stdin.") from None
        if password != confirmation:
            raise CommandError("Passwords do not match.")
    try:
        admin = AdminCreate(
            email=args.email, password=password, full_name=args.full_name, is_superuser=True
        )
    except ValidationError:
        raise CommandError("Invalid administrator details: use a valid email, an 8–72 byte password, and a name up to 150 characters.") from None
    if not password.strip() or len(password.encode("utf-8")) > 72:
        raise CommandError("Password must be nonblank and at most 72 UTF-8 bytes (bcrypt limit).")
    return admin


async def create_admin_account(session, admin: AdminCreate) -> bool:
    """Return whether an account was created; existing accounts remain untouched."""
    from sqlalchemy import func, select
    from sqlalchemy.exc import IntegrityError

    from app.core.security import hash_password
    from app.models import AdminUser

    email = str(admin.email).lower()
    existing = select(AdminUser).where(func.lower(AdminUser.email) == email)
    if await session.scalar(existing):
        return False
    session.add(
        AdminUser(
            email=email,
            full_name=admin.full_name,
            hashed_password=hash_password(admin.password),
            is_active=True,
            is_superuser=True,
        )
    )
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if await session.scalar(existing):
            return False
        raise
    return True


async def _run(command: str, admin: AdminCreate | None) -> str:
    from app.core.config import settings
    from app.core.lifecycle import check_database
    from app.db.seed import seed_portfolios
    from app.db.session import SessionFactory, engine

    try:
        await check_database(engine, settings.schema_check_timeout_seconds)
        async with SessionFactory() as session:
            if command == "create-admin":
                created = await create_admin_account(session, admin)
                return "Administrator created." if created else "Account already exists; no changes made."
            await seed_portfolios(session)
            return "Demo portfolio seed completed; existing portfolios were left unchanged."
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        admin = _read_admin(args) if args.command == "create-admin" else None
        print(asyncio.run(_run(args.command, admin)))
        return 0
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print("Command cancelled; no password was accepted.", file=sys.stderr)
    except Exception:
        print(
            "Command failed. Check required configuration, database connectivity, and "
            "permissions; run `alembic upgrade head` before bootstrap. No account was reset.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
