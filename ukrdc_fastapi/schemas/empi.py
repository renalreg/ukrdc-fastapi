import datetime
from typing import List, Optional

from fastapi_hypermodel import HyperRef
from pydantic import Json

from .base import OrmModel


class MasterRecordSchema(OrmModel):
    id: int
    last_updated: datetime.datetime
    date_of_birth: datetime.date
    gender: Optional[str]
    givenname: Optional[str]
    surname: Optional[str]
    nationalid: str
    nationalid_type: str
    status: int
    effective_date: datetime.datetime


class PidXRefSchema(OrmModel):
    id: int
    pid: str
    sending_facility: str
    sending_extract: str
    localid: str


class PersonSchema(OrmModel):
    id: int
    originator: str
    localid: str
    localid_type: str
    date_of_birth: datetime.date
    gender: str
    date_of_death: Optional[datetime.date]
    givenname: Optional[str]
    surname: Optional[str]
    xref_entries: List[PidXRefSchema]


class LinkRecordSchema(OrmModel):
    id: int
    person: PersonSchema
    master_record: MasterRecordSchema


class WorkItemSummarySchema(OrmModel):
    id: int
    person_id: int
    master_id: int
    href: HyperRef

    class Href:
        endpoint = "workitems_detail"
        values = {"workitem_id": "<id>"}


class WorkItemShortSchema(OrmModel):
    id: int
    person_id: int
    master_id: int
    type: int
    description: str
    status: int
    last_updated: datetime.datetime
    updated_by: Optional[str]
    update_description: Optional[str]
    attributes: Optional[Json]
    href: HyperRef

    class Href:
        endpoint = "workitems_detail"
        values = {"workitem_id": "<id>"}


class WorkItemSchema(WorkItemShortSchema):
    person: PersonSchema
    master_record: MasterRecordSchema

    # `related` attribute isn't part of ORM and needs to be injected
    related: Optional[List[WorkItemSummarySchema]]
