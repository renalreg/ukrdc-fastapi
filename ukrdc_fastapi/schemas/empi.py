import datetime
import json
from typing import Optional, Union

from pydantic import validator

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


class LinkRecordSummarySchema(OrmModel):
    id: int
    person_id: int
    master_id: int


class LinkRecordSchema(OrmModel):
    id: int
    person: PersonSchema
    master_record: MasterRecordSchema


WORKITEM_ATTRIBUTE_MAP: dict[str, str] = {
    "SE": "sending_extract",
    "SF": "sending_facility",
    "MRN": "localid",
    "DOB": "date_of_birth",
    "DOD": "date_of_death",
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


class WorkItemAttributes(OrmModel):
    sending_extract: Optional[str]
    sending_facility: Optional[str]
    localid: Optional[str]
    date_of_birth: Optional[str]
    date_of_death: Optional[str]
    gender: Optional[str]
    givenname: Optional[str]
    surname: Optional[str]


class WorkItemSchema(OrmModel):
    id: int

    type: int
    description: str
    status: int

    creation_date: datetime.datetime

    last_updated: datetime.datetime
    updated_by: Optional[str]

    attributes: Optional[WorkItemAttributes]
    update_description: Optional[str]

    person: Optional[PersonSchema]
    master_record: Optional[MasterRecordSchema]

    @validator("attributes", pre=True)
    def normalise_attributes(
        cls, value: Union[str, dict, WorkItemAttributes]
    ):  # pylint: disable=no-self-argument
        """
        Convert attributes JSON keys into MasterRecord property keys
        """
        # Convert raw JSON string into a dictionary
        if isinstance(value, str):
            value = json.loads(value)
        # Re-map dictionary keys
        if isinstance(value, dict):
            return {
                WORKITEM_ATTRIBUTE_MAP.get(key, key): attribute
                for key, attribute in value.items()
            }
        # Return existing value
        return value


class WorkItemIncomingSchema(OrmModel):
    person: Optional[PersonSchema] = None
    master_records: list[MasterRecordSchema] = []


class WorkItemDestinationSchema(OrmModel):
    persons: list[PersonSchema] = []
    master_record: Optional[MasterRecordSchema] = None


class WorkItemExtendedSchema(WorkItemSchema):
    incoming: WorkItemIncomingSchema
    destination: WorkItemDestinationSchema
