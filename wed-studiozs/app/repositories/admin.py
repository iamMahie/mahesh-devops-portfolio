"""AdminUser data access."""

from __future__ import annotations

from sqlalchemy import select

from app.models.admin import AdminUser
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository[AdminUser]):
    model = AdminUser

    async def get_by_email(self, email: str) -> AdminUser | None:
        stmt = select(AdminUser).where(AdminUser.email == email.lower())
        return await self.session.scalar(stmt)
