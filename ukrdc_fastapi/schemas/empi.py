import datetime
from typing import List

from .base import ORMModel


class MasterRecordSchema(ORMModel):
    id: int
    last_updated: datetime.datetime
    date_of_birth: datetime.date
    gender: str
    givenname: str
    surname: str
    nationalid: str
    nationalid_type: str
    status: int
    effective_date: datetime.datetime

    link_records: "List[LinkRecordSchema]"
    work_items: "List[WorkItemSchema]"


class PidXRefSchema(ORMModel):
    id: int
    pid: str
    sending_facility: str
    sending_extract: str
    localid: str


class PersonSchema(ORMModel):
    id: int
    originator: str
    localid: str
    localid_type: str
    date_of_birth: datetime.date
    gender: str
    date_of_death: datetime.date
    givenname: str
    surname: str
    xref_entries: List[PidXRefSchema]


class LinkRecordSchema(ORMModel):
    id: int
    person: PersonSchema
    master_record: MasterRecordSchema


class WorkItemSchema(ORMModel):
    id: int
    person_id: int
    master_id: int
    type: int
    description: str
    status: int
    updated_by: str
    update_description: str
    attributes: str
    person: PersonSchema
    master_record: MasterRecordSchema


# Update link_records and work_items annotations
MasterRecordSchema.update_forward_refs()
