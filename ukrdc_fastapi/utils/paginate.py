from typing import Generic, TypeVar

from fastapi import Query
from fastapi_pagination import paginate as paginate_sequence
from fastapi_pagination.default import Page as BasePage
from fastapi_pagination.default import Params as BaseParams
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.utils import disable_installed_extensions_check

__all__ = ["Page", "Params", "paginate", "paginate_sequence"]

T = TypeVar("T")  # pylint: disable=invalid-name

# We sometimes paginate normal lists, not just SQLAlchemy queries,
# so we need to disable the check that fastapi_pagination does
# to warn you if you use the normal pagination function when you
# have SQLAlchemy installed.
disable_installed_extensions_check()


class Params(BaseParams):
    size: int = Query(20, gt=0, le=50, description="Page size")


class Page(BasePage[T], Generic[T]):
    __params_type__ = Params
