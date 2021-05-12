from typing import Generic, TypeVar

from fastapi import Query
from fastapi_pagination.default import Page as BasePage
from fastapi_pagination.default import Params as BaseParams
from fastapi_pagination.ext.sqlalchemy import paginate, paginate_query

__all__ = ["PaginationParams", "Page", "paginate", "paginate_query"]

T = TypeVar("T")


class Params(BaseParams):
    size: int = Query(20, gt=0, le=100, description="Page size")


class Page(BasePage[T], Generic[T]):
    __params_type__ = Params
