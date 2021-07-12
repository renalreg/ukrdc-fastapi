import enum
from typing import Optional, Type

from fastapi import HTTPException
from sqlalchemy import Column
from sqlalchemy.orm import Query as ORMQuery


class OrderBy(str, enum.Enum):
    asc = "asc"
    desc = "desc"


class Sorter:
    def __init__(
        self,
        sqla_model: Type,
        column_map: dict[str, Column],
        sort_by: Optional[enum.Enum] = None,
        order_by: Optional[OrderBy] = None,
        default_sort_by: Optional[Column] = None,
        default_order_by: OrderBy = OrderBy.desc,
    ) -> None:
        self.sqla_model = sqla_model
        self.column_map = column_map
        self.sort_by = sort_by
        self.order_by = order_by
        self.default_sort_by = default_sort_by
        self.default_order_by = default_order_by

    def sort(self, query: ORMQuery):
        if not self.sort_by and not self.default_sort_by:
            return query

        sort_column: Optional[Column]
        if self.default_sort_by:
            sort_column = self.default_sort_by
        else:
            sort_column = self.column_map.get(self.sort_by.value)
            if not sort_column:
                raise HTTPException(400, f"Invalid sort key '{self.sort_by.value}'")

        if self.order_by:
            if self.order_by == OrderBy.asc:
                sort_func = sort_column.asc
            else:
                sort_func = sort_column.desc
        else:
            if self.default_order_by == OrderBy.asc:
                sort_func = sort_column.asc
            else:
                sort_func = sort_column.desc

        return query.order_by(sort_func())


def sorter(
    sqla_model: Type,
    columns: list[Column],
    default_sort_by: Optional[Column] = None,
    default_order_by: OrderBy = OrderBy.desc,
):
    column_map: dict[str, Column] = {col.key: col for col in columns}
    SortEnum = enum.Enum(
        f"{sqla_model.__name__}Enum", {col.key: col.key for col in columns}
    )

    def sort_parameters(
        sort_by: Optional[SortEnum] = None, order_by: Optional[OrderBy] = None
    ):
        return Sorter(
            sqla_model,
            column_map,
            sort_by,
            order_by,
            default_sort_by=default_sort_by,
            default_order_by=default_order_by,
        )

    return sort_parameters
