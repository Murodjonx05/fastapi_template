from typing import Type, TypeVar, Generic, Any, Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class CRUDBase(Generic[T]):
    """Minimized generic store for standard ORM operations."""
    def __init__(self, model: Type[T]):
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> T | None:
        return await session.get(self.model, id)

    async def get_by_field(self, session: AsyncSession, **kwargs) -> T | None:
        return await session.scalar(select(self.model).filter_by(**kwargs))

    async def list(self, session: AsyncSession, offset: int = 0, limit: int = 20) -> Sequence[T]:
        return (await session.execute(select(self.model).offset(offset).limit(limit))).scalars().all()

    async def create(self, session: AsyncSession, data: dict[str, Any]) -> T:
        obj = self.model(**data)
        session.add(obj)
        await session.flush()
        return obj

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        return (await session.execute(delete(self.model).where(self.model.id == id))).rowcount > 0
