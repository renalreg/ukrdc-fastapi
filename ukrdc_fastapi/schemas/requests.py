import datetime
from typing import Optional

from pydantic import Field

from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.patientrecord.patient import (
    AddressSchema,
    GenderType,
    NameSchema,
)


class DemographicUpdateRequest(JSONModel):
    name: Optional[NameSchema] = None
    birth_time: Optional[datetime.datetime] = None
    gender: Optional[GenderType] = None
    address: Optional[AddressSchema] = None


class CloseWorkItemRequest(JSONModel):
    comment: Optional[str] = Field(None, max_length=100)


class UpdateWorkItemRequest(JSONModel):
    status: Optional[int] = None
    comment: Optional[str] = Field(None, max_length=100)


class MergeRequest(JSONModel):
    superseding: int = Field(..., title="Superseding master-record ID")
    superseded: int = Field(..., title="Superseded master-record ID")


class UnlinkRequest(JSONModel):
    person_id: int = Field(..., title="ID of the person-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")
    comment: Optional[str] = Field(None, max_length=100)


class UnlinkPatientRequest(JSONModel):
    pid: str = Field(..., title="PID of the patient-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")
