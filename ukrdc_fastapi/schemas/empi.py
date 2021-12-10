import datetime
from typing import Optional, Union

from fastapi_hypermodel import LinkSet, UrlFor
from pydantic import Json, validator

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
            "latestMessage": UrlFor(
                "master_record_latest_message", {"record_id": "<id>"}
            ),
            "statistics": UrlFor("master_record_statistics", {"record_id": "<id>"}),
            "related": UrlFor("master_record_related", {"record_id": "<id>"}),
            "messages": UrlFor("master_record_messages", {"record_id": "<id>"}),
            "linkrecords": UrlFor("master_record_linkrecords", {"record_id": "<id>"}),
            "persons": UrlFor("master_record_persons", {"record_id": "<id>"}),
            "workitems": UrlFor("master_record_workitems", {"record_id": "<id>"}),
            "patientrecords": UrlFor(
                "master_record_patientrecords", {"record_id": "<id>"}
            ),
            "audit": UrlFor("master_record_audit", {"record_id": "<id>"}),
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
    xref_entries: list[PidXRefSchema]

    links = LinkSet(
        {
            "self": UrlFor("person_detail", {"person_id": "<id>"}),
            "patientrecord": UrlFor("patient_get", {"pid": "<localid>"}),
            "masterrecords": UrlFor("person_masterrecords", {"person_id": "<id>"}),
        }
    )


class LinkRecordSummarySchema(OrmModel):
    id: int
    person_id: int
    master_id: int


class LinkRecordSchema(OrmModel):
    id: int
    person: PersonSchema
    master_record: MasterRecordSchema


WORKITEM_ATTRIBUTE_MAP: dict[str, str] = {
    "SE": "sendingExtract",
    "SF": "sendingFacility",
    "MRN": "localid",
    "DOB": "dateOfBirth",
    "DOD": "dateOfDeath",
    "Gender": "gender",
    "GivenName": "givenname",
    "Surname": "surname",
}


class WorkItemSummarySchema(OrmModel):
    id: int
    person_id: int
    master_id: int
    type: int
    status: int


class WorkItemSchema(OrmModel):
    id: int

    type: int
    description: str
    status: int

    creation_date: datetime.datetime

    last_updated: datetime.datetime
    updated_by: Optional[str]

    attributes: Optional[Union[Json, dict]]
    update_description: Optional[str]

    person: Optional[PersonSchema]
    master_record: Optional[MasterRecordSchema]

    links = LinkSet(
        {
            "self": UrlFor("workitem_detail", {"workitem_id": "<id>"}),
            "collection": UrlFor("workitem_collection", {"workitem_id": "<id>"}),
            "related": UrlFor("workitem_related", {"workitem_id": "<id>"}),
            "messages": UrlFor("workitem_messages", {"workitem_id": "<id>"}),
            "close": UrlFor("workitem_close", {"workitem_id": "<id>"}),
        }
    )

    @validator("attributes")
    def normalise_attributes(
        cls, value
    ):  # pylint: disable=no-self-argument,no-self-use
        """
        Convert attributes JSON keys into MasterRecord property keys
        """
        if not isinstance(value, dict):
            return value
        return {
            WORKITEM_ATTRIBUTE_MAP.get(key, key): attribute
            for key, attribute in value.items()
        }


class WorkItemIncomingSchema(OrmModel):
    person: Optional[PersonSchema] = None
    master_records: list[MasterRecordSchema] = []


class WorkItemDestinationSchema(OrmModel):
    persons: list[PersonSchema] = []
    master_record: Optional[MasterRecordSchema] = None


class WorkItemExtendedSchema(WorkItemSchema):
    incoming: WorkItemIncomingSchema
    destination: WorkItemDestinationSchema
