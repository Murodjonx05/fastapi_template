from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError

from src.crud.base import CRUDBase
from src.database import AsyncSession, AsyncSessionMaker

if TYPE_CHECKING:
    from src.database import AuditLog

logger = logging.getLogger(__name__)


class AuditLogCRUD(CRUDBase):
    """CRUD for audit logs."""

    def __init__(self) -> None:
        from src.database import AuditLog

        super().__init__(AuditLog)

    async def create_log(
        self,
        session: AsyncSession,
        action: str,
        user_id: int | None,
        target_type: str | None = None,
        target_id: int | None = None,
        details: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "AuditLog | None":
        """Create an audit log entry.

        Uses a separate session to avoid interfering with the main transaction.
        Returns None on failure.
        """
        # Use a completely separate session to avoid any transaction coupling
        async with AsyncSessionMaker() as audit_session:
            log_data = {
                "action": action,
                "user_id": user_id,
                "target_type": target_type,
                "target_id": target_id,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
            try:
                obj = self.model(**log_data)
                audit_session.add(obj)
                await audit_session.commit()
                return obj
            except SQLAlchemyError as exc:
                logger.warning(
                    f"Failed to create audit log for action '{action}': {exc}"
                )
                await audit_session.rollback()
                return None


audit_log_crud = AuditLogCRUD()
