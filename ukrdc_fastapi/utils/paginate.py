from __future__ import annotations

from typing import Generic, Optional, Sequence, TypeVar

from fastapi_pagination import use_as_page
from fastapi_pagination.api import create_page, resolve_params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic import Field
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

Q = TypeVar("Q", Select, Query)
T = TypeVar("T")


@use_as_page
class Page(AbstractPage[T], Generic[T]):
    items: Sequence[T]
    page: int = Field(..., ge=0)
    size: int = Field(..., gt=0)

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        _: Optional[int],
        params: AbstractParams,
    ) -> Page[T]:
        return cls(
            items=items,
            page=params.page,
            size=params.size,
        )


def paginate_query(query: Q, params: AbstractParams) -> Q:
    params = params.to_limit_offset()
    return query.limit(params.limit).offset(params.offset)


def paginate(query: Query, params: Optional[AbstractParams] = None) -> AbstractPage:
    params = resolve_params(params)
    items = paginate_query(query, params).all()
    return create_page(items, None, params)
