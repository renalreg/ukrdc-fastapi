import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor

from .base import OrmModel


class LabOrderShortSchema(OrmModel):
    id: str
    entered_at_description: Optional[str]
    entered_at: Optional[str]
    specimen_collected_time: datetime.datetime

    links = LinkSet({"self": UrlFor("laborder_get", {"order_id": "<id>"})})


class ResultItemSchema(OrmModel):
    id: str
    order_id: str
    service_id: str
    service_id_description: str
    value: str
    value_units: Optional[str]
    result_type: Optional[str]
    observation_time: datetime.datetime

    links = LinkSet(
        {
            "self": UrlFor("resultitem_detail", {"resultitem_id": "<id>"}),
            "laborder": UrlFor("laborder_get", {"order_id": "<order_id>"}),
        }
    )


class ResultItemServiceSchema(OrmModel):
    id: str
    description: str
    standard: str


class LabOrderSchema(LabOrderShortSchema):
    result_items: Optional[list[ResultItemSchema]]
