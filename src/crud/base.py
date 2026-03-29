from typing import Type, TypeVar, Generic, Sequence, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import BasePK

ModelT = TypeVar("ModelT", bound=BasePK)

class CRUDBase(Generic[ModelT]):
    """Generic CRUD operations for standard ORM models."""
    def __init__(self, model: Type[ModelT]):
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> ModelT | None:
        return await session.get(self.model, id)

    async def get_by_field(self, session: AsyncSession, field: str, value: Any) -> ModelT | None:
        attr = getattr(self.model, field)
        return await session.scalar(select(self.model).where(attr == value))

    async def list(self, session: AsyncSession, *, offset: int = 0, limit: int = 20) -> Sequence[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await session.execute(stmt)
        return result.rowcount > 0
