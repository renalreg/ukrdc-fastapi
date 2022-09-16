import datetime
import json
from typing import Optional, Union

from pydantic import Field, validator

from .base import OrmModel


class MasterRecordSchema(OrmModel):
    """A master record in the EMPI"""

    id: int = Field(..., description="Master record ID")
    nationalid: str = Field(..., description="National ID, e.g. NHS number")
    nationalid_type: str = Field(
        ..., description="National ID type, e.g. NHS, CHI, HSC, UKRDC"
    )
    last_updated: datetime.datetime = Field(
        ..., description="EMPI record last updated timestamp"
    )
    date_of_birth: datetime.date = Field(..., description="Patient date of birth")
    gender: Optional[str] = Field(None, description="Patient gender code")
    givenname: Optional[str] = Field(None, description="Patient given name")
    surname: Optional[str] = Field(None, description="Patient surname")
    status: int = Field(..., description="EMPI record status code")
    effective_date: datetime.datetime


class PidXRefSchema(OrmModel):
    """A PID cross-reference in the EMPI"""

    id: int = Field(..., description="PID xref ID")
    pid: str = Field(..., description="Patient record PID")
    sending_facility: str = Field(..., description="Sending facility code")
    sending_extract: str = Field(..., description="Sending extract code")
    localid: str = Field(..., description="Person local ID")


class PersonSchema(OrmModel):
    """A person in the EMPI"""

    id: int = Field(..., description="Person ID")
    originator: str = Field(..., description="Person originator code")
    localid: str = Field(..., description="Person local ID")
    localid_type: str = Field(..., description="Person local ID type code")
    date_of_birth: datetime.date = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender code")
    date_of_death: Optional[datetime.date] = Field(None, description="Date of death")
    givenname: Optional[str] = Field(None, description="Given name")
    surname: Optional[str] = Field(None, description="Surname")
    xref_entries: list[PidXRefSchema] = Field(..., description="PID xrefs")


class LinkRecordSummarySchema(OrmModel):
    """Summary of a link record in the EMPI, linking a person to a master record"""

    id: int = Field(..., description="Link record ID")
    person_id: int = Field(..., description="Person ID")
    master_id: int = Field(..., description="Master record ID")


class LinkRecordSchema(OrmModel):
    """A link record in the EMPI, linking a person to a master record"""

    id: int = Field(..., description="Link record ID")
    person: PersonSchema = Field(..., description="Person record")
    master_record: MasterRecordSchema = Field(..., description="Master record")


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
    """Summary of a work item in the EMPI"""

    id: int = Field(..., description="Work item ID")
    person_id: int = Field(..., description="Person ID")
    master_id: int = Field(..., description="Master record ID")
    type: int = Field(..., description="Work item type code")
    status: int = Field(..., description="Work item status code")


class WorkItemAttributes(OrmModel):
    """
    Attributes of the incoming record that mismatch the destination EMPI record, in the format incoming:destination
    """

    sending_extract: Optional[str] = Field(
        None, description="Mismatching sending extract values"
    )
    sending_facility: Optional[str] = Field(
        None, description="Mismatching sending facility values"
    )
    localid: Optional[str] = Field(None, description="Mismatching local ID values")
    date_of_birth: Optional[str] = Field(
        None, description="Mismatching date of birth values"
    )
    date_of_death: Optional[str] = Field(
        None, description="Mismatching date of death values"
    )
    gender: Optional[str] = Field(None, description="Mismatching gender code values")
    givenname: Optional[str] = Field(None, description="Mismatching given name values")
    surname: Optional[str] = Field(None, description="Mismatching surname values")


class WorkItemSchema(OrmModel):
    """A work item in the EMPI"""

    id: int = Field(..., description="Work item ID")

    type: int = Field(..., description="Work item type code")
    description: str = Field(..., description="Work item description")
    status: int = Field(..., description="Work item status code")

    creation_date: datetime.datetime = Field(
        ..., description="Work item creation timestamp"
    )

    last_updated: datetime.datetime = Field(
        ..., description="Work item last updated timestamp"
    )
    updated_by: Optional[str] = Field(
        None, description="Work item last updated by username"
    )

    attributes: Optional[WorkItemAttributes] = Field(
        None, description="Work item mismatching attributes"
    )
    update_description: Optional[str] = Field(
        None, description="Description of the reaoning behind the last update"
    )

    person: Optional[PersonSchema] = Field(None, description="Person record")
    master_record: Optional[MasterRecordSchema] = Field(
        None, description="Master record"
    )

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
    """Incoming records for a work item in the EMPI"""

    person: Optional[PersonSchema] = Field(None, description="Person record")
    master_records: list[MasterRecordSchema] = Field(..., description="Master records")


class WorkItemDestinationSchema(OrmModel):
    """Destination records for a work item in the EMPI"""

    persons: list[PersonSchema] = Field(..., description="Person records")
    master_record: Optional[MasterRecordSchema] = Field(
        None, description="Master record"
    )


class WorkItemExtendedSchema(WorkItemSchema):
    """A work item in the EMPI, with additional record information"""

    incoming: WorkItemIncomingSchema = Field(..., description="Incoming records")
    destination: WorkItemDestinationSchema = Field(
        ..., description="Destination records"
    )
