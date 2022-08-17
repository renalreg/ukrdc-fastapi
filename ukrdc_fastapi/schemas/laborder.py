import datetime
from typing import Optional

from .base import OrmModel


class LabOrderShortSchema(OrmModel):
    id: str
    pid: str

    entered_at_description: Optional[str]
    entered_at: Optional[str]
    specimen_collected_time: Optional[datetime.datetime]


class ResultItemSchema(OrmModel):
    id: str
    pid: str

    order_id: str
    service_id: str
    service_id_description: Optional[str]
    value: Optional[str]
    value_units: Optional[str]
    result_type: Optional[str]
    pre_post: Optional[str]
    observation_time: Optional[datetime.datetime]


class ResultItemServiceSchema(OrmModel):
    id: str
    description: Optional[str]
    standard: str


class LabOrderSchema(LabOrderShortSchema):
    result_items: list[ResultItemSchema]
