"""Generic async repository: the only layer that talks to SQLAlchemy."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------------------------------------------------------- reads
    async def get(self, entity_id: int) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        statement: Select | None = None,
    ) -> list[ModelT]:
        stmt = statement if statement is not None else select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.unique().all())

    async def count(self, statement: Select | None = None) -> int:
        base = statement if statement is not None else select(self.model)
        # `order_by` breaks some count subqueries on PostgreSQL -> strip it.
        subquery = base.order_by(None).subquery()
        return await self.session.scalar(select(func.count()).select_from(subquery)) or 0

    async def exists(self, **filters: Any) -> bool:
        stmt = select(self.model.id).filter_by(**filters).limit(1)
        return await self.session.scalar(stmt) is not None

    # --------------------------------------------------------------- writes
    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        return entity

    async def create(self, **values: Any) -> ModelT:
        entity = self.model(**values)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: ModelT, values: dict[str, Any]) -> ModelT:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, entity: ModelT) -> ModelT:
        await self.session.refresh(entity)
        return entity
