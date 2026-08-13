"""Base repository with shared CRUD helpers."""

from __future__ import annotations

from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    model: Type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: str) -> Optional[T]:
        return await self.session.get(self.model, id_)

    async def get_many(self, ids: Sequence[str]) -> List[T]:
        if not ids:
            return []
        stmt = select(self.model).where(self.model.id.in_(list(ids)))  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def add_all(self, objs: Sequence[T]) -> List[T]:
        self.session.add_all(list(objs))
        await self.session.flush()
        return list(objs)

    async def delete(self, obj: T) -> None:
        await self.session.delete(obj)
