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
    name: NameSchema | None = None
    birth_time: datetime.datetime | None = None
    gender: GenderType | None = None
    address: AddressSchema | None = None


class CloseWorkItemRequest(JSONModel):
    comment: str | None = Field(None, max_length=100)


class UpdateWorkItemRequest(JSONModel):
    status: int | None = None
    comment: str | None = Field(None, max_length=100)


class MergeRequest(JSONModel):
    superseding: int = Field(..., title="Superseding master-record ID")
    superseded: int = Field(..., title="Superseded master-record ID")


class UnlinkRequest(JSONModel):
    person_id: int = Field(..., title="ID of the person-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")
    comment: str | None = Field(None, max_length=100)


class UnlinkPatientRequest(JSONModel):
    pid: str = Field(..., title="PID of the patient-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")
