from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict

Pagination = Annotated[int, Query(ge=1, description="Page number", examples=[1])]
PaginationCount = Annotated[
    int, Query(ge=1, le=100, description="Items per page", examples=[20])
]


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class PaginationSchema(BaseSchema):
    page: Pagination = 1
    count: PaginationCount = 20


PaginationSchemaDep = Annotated[PaginationSchema, Depends(PaginationSchema)]
