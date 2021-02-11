import datetime
from typing import List

from .base import ORMModel


class LabOrderShortSchema(ORMModel):
    id: str
    entered_at_description: str
    entered_at: str
    specimen_collected_time: datetime.datetime


class ResultItemSchema(ORMModel):
    id: str
    order_id: str
    service_id: str
    service_id_description: str
    value: str
    value_units: str


class LabOrderSchema(LabOrderShortSchema):
    results: List[ResultItemSchema]
