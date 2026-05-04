from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class AuditLogBaseSchema(BaseModel):
    action: Annotated[
        str,
        Query(description="Action type (e.g., user_created, login, delete)"),
    ]
    user_id: Annotated[
        int | None, Query(description="ID of the user who performed the action")
    ]
    target_type: Annotated[
        str | None, Query(description="Type of target (user, role, permission)")
    ]
    target_id: Annotated[int | None, Query(description="ID of the target entity")]
    details: Annotated[
        str | None, Query(description="Additional details about the action")
    ]
    ip_address: Annotated[
        str | None, Query(description="IP address where action originated")
    ]
    user_agent: Annotated[str | None, Query(description="User agent string")]

    model_config = ConfigDict(from_attributes=True)


class AuditLogCreateSchema(AuditLogBaseSchema):
    pass


class AuditLogResponseSchema(AuditLogBaseSchema):
    id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogListSchema(BaseModel):
    items: list[AuditLogResponseSchema]
    total: int
    page: int
    count: int
