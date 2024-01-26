import enum
import functools
from typing import Any, Optional, Union

from fastapi import HTTPException
from sqlalchemy import Column
from sqlalchemy.orm import Query
from sqlalchemy.sql.selectable import Select


def rgetattr(obj, attr, *args):
    """Recursive getattr, i.e. when passed a . separated attribute name, gets the value from nested objects.

    Args:
        obj (Any): Target object
        attr (str): Attribute name(s)
    """

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


class OrderBy(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class SQLASorter:
    def __init__(
        self,
        column_map: dict[str, Column],
        sort_by: Optional[enum.Enum] = None,
        order_by: Optional[OrderBy] = None,
        default_sort_by: Optional[Column] = None,
        default_order_by: OrderBy = OrderBy.DESC,
    ) -> None:
        self.column_map = column_map
        self.sort_by = sort_by
        self.order_by = order_by
        self.default_sort_by = default_sort_by
        self.default_order_by = default_order_by

    def sort(self, query: Union[Query, Select]):
        """Sort an SQLAlchemy query by the paremeters obtained from FastAPI

        Args:
            query (sqlalchemy.orm.Query): Unsorted query

        Returns:
            query (sqlalchemy.orm.Query): Sorted query
        """
        sort_column: Optional[Column]
        if self.sort_by:
            sort_column = self.column_map.get(self.sort_by.value)
            if not sort_column:
                raise HTTPException(400, f"Invalid sort key '{self.sort_by.value}'")
        elif self.default_sort_by:
            sort_column = self.default_sort_by
        else:
            return query

        if self.order_by:
            if self.order_by == OrderBy.ASC:
                sort_func = sort_column.asc
            else:
                sort_func = sort_column.desc
        else:
            if self.default_order_by == OrderBy.ASC:
                sort_func = sort_column.asc
            else:
                sort_func = sort_column.desc

        return query.order_by(sort_func())


def _make_sorter_enum_name(columns: list[Union[Column, str]]) -> str:
    modelnames = set()
    for col in columns:
        cls = str(col).split(".", maxsplit=1)[0]
        modelnames.add(cls)
    return "".join(modelnames) + "Enum"


def make_sqla_sorter(
    columns: list[Column],
    default_sort_by: Optional[Column] = None,
    default_order_by: OrderBy = OrderBy.DESC,
):
    """Generate a sorter FastAPI dependency function

    Args:
        columns (list[Column]): SQLAlchemy columns to allow sorting by
        default_sort_by (Optional[Column]): Default sort column. Defaults to None.
        default_order_by (OrderBy, optional): Default sort direction. Defaults to OrderBy.DESC.

    Returns:
        [function]: FastAPI dependency function returning a SQLASorter instance
    """
    column_map: dict[str, Column] = {col.key: col for col in columns}
    sort_enum = enum.Enum(  # type: ignore
        _make_sorter_enum_name(columns), {col.key: col.key for col in columns}
    )

    def sort_parameters(
        sort_by: Optional[sort_enum] = None, order_by: Optional[OrderBy] = None
    ):
        return SQLASorter(
            column_map,
            sort_by,
            order_by,
            default_sort_by=default_sort_by,
            default_order_by=default_order_by,
        )

    return sort_parameters


class ObjectSorter:
    def __init__(
        self,
        columns: list[str],
        sort_by: Optional[enum.Enum] = None,
        order_by: Optional[OrderBy] = None,
        default_sort_by: Optional[str] = None,
        default_order_by: OrderBy = OrderBy.DESC,
    ) -> None:
        self.columns = columns
        self.sort_by = sort_by
        self.order_by = order_by
        self.default_sort_by = default_sort_by
        self.default_order_by = default_order_by

    def sort(self, items: list[Any]):
        """Sort a list of objects by the paremeters obtained from FastAPI

        Args:
            items (list[Any]): Unsorted list of objects

        Returns:
            items (list[Any]): Sorted list of objects
        """

        sort_attr: Optional[str] = (
            self.sort_by.name if self.sort_by else self.default_sort_by
        )
        if not sort_attr:
            return items

        if sort_attr not in self.columns:
            raise HTTPException(400, f"Invalid sort key '{self.sort_by}'")

        def keyfunc(item: Any) -> Any:
            """Sort key function, see https://stackoverflow.com/a/48235298"""
            value = rgetattr(item, sort_attr)
            return (value is not None, value)

        return sorted(
            items,
            key=keyfunc,
            reverse=(self.order_by or self.default_order_by) == OrderBy.DESC,
        )


def make_object_sorter(
    name: str,
    columns: list[str],
    default_sort_by: Optional[str] = None,
    default_order_by: OrderBy = OrderBy.DESC,
):
    """Generate a sorter FastAPI dependency function

    Args:
        columns (list[str]): Attribute names to allow sorting by
        default_sort_by (Optional[str]): Default sort attribute. Defaults to None.
        default_order_by (OrderBy, optional): Default sort direction. Defaults to OrderBy.DESC.

    Returns:
        [function]: FastAPI dependency function returning an ObjectSorter instance
    """
    sort_enum = enum.Enum(name, {col: col for col in columns})  # type: ignore

    def sort_parameters(
        sort_by: Optional[sort_enum] = None, order_by: Optional[OrderBy] = None
    ):
        return ObjectSorter(
            columns,
            sort_by,
            order_by,
            default_sort_by=default_sort_by,
            default_order_by=default_order_by,
        )

    return sort_parameters
