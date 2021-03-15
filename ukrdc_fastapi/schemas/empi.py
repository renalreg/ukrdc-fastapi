import datetime
from typing import List, Optional

from fastapi_hypermodel import LinkSet, UrlFor
from pydantic import Json

from .base import OrmModel


class MasterRecordSchema(OrmModel):
    id: int
    nationalid: str
    nationalid_type: str
    last_updated: datetime.datetime
    date_of_birth: datetime.date
    gender: Optional[str]
    givenname: Optional[str]
    surname: Optional[str]
    status: int
    effective_date: datetime.datetime

    links = LinkSet(
        {
            "self": UrlFor("master_record_detail", {"record_id": "<id>"}),
            "related": UrlFor("master_record_related", {"record_id": "<id>"}),
            "persons": UrlFor("master_record_persons", {"record_id": "<id>"}),
            "workitems": UrlFor("master_record_workitems", {"record_id": "<id>"}),
            "patientrecords": UrlFor(
                "master_record_patientrecords", {"record_id": "<id>"}
            ),
        }
    )


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

    links = LinkSet(
        {
            "self": UrlFor("person_detail", {"person_id": "<id>"}),
            "patientrecord": UrlFor("patient_record", {"pid": "<localid>"}),
            "masterrecords": UrlFor("person_masterrecords", {"person_id": "<id>"}),
        }
    )


class LinkRecordSchema(OrmModel):
    id: int
    person: PersonSchema
    master_record: MasterRecordSchema


class WorkItemSummarySchema(OrmModel):
    id: int
    person_id: int
    master_id: int

    links = LinkSet(
        {
            "self": UrlFor("workitem_detail", {"workitem_id": "<id>"}),
            "related": UrlFor("workitem_related", {"workitem_id": "<id>"}),
            "close": UrlFor("workitem_close", {"workitem_id": "<id>"}),
            "merge": UrlFor("workitem_merge", {"workitem_id": "<id>"}),
        }
    )


class WorkItemShortSchema(WorkItemSummarySchema):
    type: int
    description: str
    status: int
    last_updated: datetime.datetime
    updated_by: Optional[str]
    update_description: Optional[str]
    attributes: Optional[Json]


class WorkItemSchema(WorkItemShortSchema):
    person: Optional[PersonSchema]
    master_record: Optional[MasterRecordSchema]
