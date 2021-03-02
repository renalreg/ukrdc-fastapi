from __future__ import annotations

from typing import Generic, Optional, Sequence, TypeVar

from fastapi_pagination import use_as_page
from fastapi_pagination.api import create_page, resolve_params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic import conint
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

Q = TypeVar("Q", Select, Query)  # pylint: disable=invalid-name
T = TypeVar("T")  # pylint: disable=invalid-name


@use_as_page
class Page(AbstractPage[T], Generic[T]):  # pylint: disable=too-many-ancestors
    items: Sequence[T]
    page: conint(ge=0)  # type: ignore
    size: conint(gt=0)  # type: ignore

    @classmethod
    def create(  # pylint: disable=missing-function-docstring
        cls,
        items: Sequence[T],
        _: Optional[int],
        params: AbstractParams,
    ) -> Page[T]:
        return cls(
            items=items,
            page=getattr(params, "page", 0),
            size=getattr(params, "size", 50),
        )


def paginate_query(query: Q, params: AbstractParams) -> Q:
    """Paginate an SQLAlchemy query based on passed params object

    Args:
        query (Q): Query object
        params (AbstractParams): AbstractParams instance

    Returns:
        Q: Paginated query
    """
    params = params.to_limit_offset()
    return query.limit(params.limit).offset(params.offset)


def paginate(query: Query, params: Optional[AbstractParams] = None) -> AbstractPage:
    """Resolve params from FastAPI dependency, and paginate query

    Args:
        query (Query): Query object
        params (Optional[AbstractParams], optional): AbstractParams instance.
            Defaults to None.

    Returns:
        AbstractPage: Page object containing items and pagination info
    """
    params = resolve_params(params)
    items = paginate_query(query, params).all()
    return create_page(items, 0, params)
