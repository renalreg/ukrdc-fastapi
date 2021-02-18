import datetime
from typing import List, Optional

from .base import OrmModel


class LabOrderShortSchema(OrmModel):
    id: str
    entered_at_description: Optional[str]
    entered_at: Optional[str]
    specimen_collected_time: datetime.datetime


class ResultItemSchema(OrmModel):
    id: str
    order_id: str
    service_id: str
    service_id_description: str
    value: str
    value_units: str


class LabOrderSchema(LabOrderShortSchema):
    results: List[ResultItemSchema]
