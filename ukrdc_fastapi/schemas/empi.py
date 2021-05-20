import datetime
from typing import Optional

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
            "statistics": UrlFor("master_record_statistics", {"record_id": "<id>"}),
            "related": UrlFor("master_record_related", {"record_id": "<id>"}),
            "errors": UrlFor("master_record_errors", {"record_id": "<id>"}),
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
    xref_entries: list[PidXRefSchema]

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


class WorkItemShortSchema(OrmModel):
    id: int

    type: int
    description: str
    status: int
    last_updated: datetime.datetime
    updated_by: Optional[str]

    person: Optional[PersonSchema]
    master_record: Optional[MasterRecordSchema]

    links = LinkSet(
        {
            "self": UrlFor("workitem_detail", {"workitem_id": "<id>"}),
            "related": UrlFor("workitem_related", {"workitem_id": "<id>"}),
            "errors": UrlFor("workitem_errors", {"workitem_id": "<id>"}),
            "close": UrlFor("workitem_close", {"workitem_id": "<id>"}),
            "merge": UrlFor("workitem_merge", {"workitem_id": "<id>"}),
            "unlink": UrlFor("workitem_unlink", {"workitem_id": "<id>"}),
        }
    )


WORKITEM_ATTRIBUTE_MAP: dict[str, str] = {
    "SE": "sendingExtract",
    "SF": "sendingFacility",
    "MRN": "localid",
    "DOB": "dateOfBirth",
    "DOD": "dateOfDeath",
    "Gender": "gender",
    "name": "givenname",
    "GivenName": "givenname",
    "surname": "surname",
}


class WorkItemSchema(WorkItemShortSchema):
    attributes: Optional[Json]
    update_description: Optional[str]

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
