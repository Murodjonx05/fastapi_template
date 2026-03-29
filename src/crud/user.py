from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_and_update_password
from src.crud.base import CRUDBase
from src.models.user import User
from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema
from src.utils.db_errors import ConstraintViolationKind, get_constraint_violation_kind

# Exceptions
class UserError(Exception): """Base exception for user errors."""
class UserAlreadyExistsError(UserError): pass
class UserNotFoundError(UserError): pass
class InvalidCredentialsError(UserError): pass

class UserCRUD(CRUDBase[User]):
    """Specialized CRUD for User including authentication."""
    
    async def create(self, user: UserCreateSchema, session: AsyncSession) -> str:
        try:
            hashed = await hash_password(user.password)
            stmt = insert(User).values(username=user.username, password=hashed).returning(User.uuid)
            return (await session.execute(stmt)).scalar_one()
        except IntegrityError as e:
            if get_constraint_violation_kind(e, message_markers=("users.username",)) == ConstraintViolationKind.UNIQUE:
                raise UserAlreadyExistsError(f"User '{user.username}' already exists") from e
            raise

    async def authenticate(self, user: UserAuthSchema, session: AsyncSession) -> str:
        db_user = await self.get_by_field(session, "username", user.username)
        if not db_user: raise InvalidCredentialsError()
        
        valid, updated = await verify_and_update_password(user.password, db_user.password)
        if not valid: raise InvalidCredentialsError()
        
        if updated:
            db_user.password = updated
            await session.flush()
        return db_user.uuid

user_crud = UserCRUD(User)
