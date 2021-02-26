import datetime
from typing import List, Optional

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

    links = LinkSet({"self": UrlFor("resultitem_detail", {"resultitem_id": "<id>"})})


class LabOrderSchema(LabOrderShortSchema):
    result_items: List[ResultItemSchema]
