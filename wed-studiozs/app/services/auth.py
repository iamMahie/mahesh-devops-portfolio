"""Admin authentication: credential checks and JWT issuing."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, PermissionDeniedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.admin import AdminUser
from app.repositories.admin import AdminRepository
from app.schemas.auth import AdminCreate, Token


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AdminRepository(session)

    async def authenticate(self, email: str, password: str) -> AdminUser:
        admin = await self.repo.get_by_email(email)
        # Always run a hash comparison to keep the response time uniform.
        placeholder = "$2b$12$" + "." * 53
        if not verify_password(password, admin.hashed_password if admin else placeholder):
            raise AuthenticationError("Incorrect email or password.")
        if admin is None:
            raise AuthenticationError("Incorrect email or password.")
        if not admin.is_active:
            raise PermissionDeniedError("This admin account is disabled.")
        return admin

    async def login(self, email: str, password: str) -> Token:
        admin = await self.authenticate(email, password)
        token, expires_in = create_access_token(admin.email)
        return Token(access_token=token, expires_in=expires_in)

    async def resolve_token(self, token: str) -> AdminUser:
        payload = decode_access_token(token)
        admin = await self.repo.get_by_email(str(payload["sub"]))
        if admin is None:
            raise AuthenticationError("Account for this token no longer exists.")
        if not admin.is_active:
            raise PermissionDeniedError("This admin account is disabled.")
        return admin

    async def register_admin(self, payload: AdminCreate) -> AdminUser:
        if await self.repo.get_by_email(payload.email):
            raise ConflictError(f"Admin '{payload.email}' already exists.")
        admin = await self.repo.create(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            is_active=True,
            is_superuser=payload.is_superuser,
        )
        await self.session.commit()
        await self.session.refresh(admin)
        return admin
