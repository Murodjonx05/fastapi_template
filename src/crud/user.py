from __future__ import annotations
from typing import TYPE_CHECKING, Any
from sqlalchemy.exc import IntegrityError
from src.crud.base import CRUDBase
from src.models.user import User
from src.core.security import hash_password, verify_password

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.schemas.user import UserAuthSchema, UserCreateSchema

class UserError(Exception): pass
class UserAlreadyExistsError(UserError): pass
class UserNotFoundError(UserError): 
    def __init__(self, identifier: Any): super().__init__(f"User not found: {identifier}")
class InvalidCredentialsError(UserError): pass

class UserCRUD(CRUDBase[User]):
    """Optimized User service with authentication and registration logic."""
    def __init__(self): super().__init__(User)

    async def authenticate(self, auth: UserAuthSchema, session: AsyncSession) -> str:
        if not (user := await self.get_by_field(session, username=auth.username)):
             raise UserNotFoundError(auth.username)
        if not await verify_password(auth.password, user.password):
             raise InvalidCredentialsError()
        return str(user.uuid)

    async def create(self, data: UserCreateSchema, session: AsyncSession) -> str:
        try:
            hashed = await hash_password(data.password)
            dump = data.model_dump(exclude={"password", "password_confirm"})
            user = await super().create(session, {**dump, "password": hashed})
            return str(user.uuid)
        except IntegrityError: 
            raise UserAlreadyExistsError()

user_crud = UserCRUD()
