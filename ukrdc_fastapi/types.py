from __future__ import annotations

from typing import Any, TypeAlias, Union

from sqlalchemy.sql.schema import Column as SAColumn

from ukrdc_sqla.ukrdc import Column as UKColumn

ColumnLike: TypeAlias = Union[SAColumn[Any], UKColumn]

StrOrColumn: TypeAlias = Union[str, ColumnLike]
IntOrColumn: TypeAlias = Union[int, ColumnLike]
StrIntOrColumn: TypeAlias = Union[str, int, ColumnLike]
