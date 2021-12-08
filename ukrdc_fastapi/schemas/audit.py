import datetime
from typing import List, Optional

from pydantic.fields import Field

from .base import OrmModel


class AccessEventSchema(OrmModel):
    id: int = Field(alias="event")
    time: datetime.datetime

    user_id: str = Field(alias="uid")
    client_id: str = Field(alias="cid")
    user_email: str = Field(alias="sub")

    path: str
    method: str
    body: Optional[str]


class AuditEventSchema(OrmModel):
    id: int
    access_event: AccessEventSchema

    resource: Optional[str]
    resource_id: Optional[str]

    operation: str

    children: Optional[List["AuditEventSchema"]]


AuditEventSchema.update_forward_refs()
