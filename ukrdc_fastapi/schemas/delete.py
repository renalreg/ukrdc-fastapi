from typing import Optional

from pydantic import Field

from ukrdc_fastapi.schemas.empi import (
    LinkRecordSummarySchema,
    MasterRecordSchema,
    PersonSchema,
    PidXRefSchema,
    WorkItemSummarySchema,
)
from ukrdc_fastapi.schemas.patientrecord import PatientRecordFullSchema

from .base import OrmModel


class DeletePidRequest(OrmModel):
    hash: Optional[str] = Field(None, description="Hash of the record to delete")


class DeletePidFromEmpiRequest(OrmModel):
    persons: list[PersonSchema] = Field(..., description="Persons to delete")
    master_records: list[MasterRecordSchema] = Field(
        ..., description="Master records to delete"
    )
    pidxrefs: list[PidXRefSchema] = Field(..., description="PID xrefs to delete")
    work_items: list[WorkItemSummarySchema] = Field(
        ..., description="Work items to delete"
    )
    link_records: list[LinkRecordSummarySchema] = Field(
        ..., description="Link records to delete"
    )


class DeletePIDPreviewSchema(OrmModel):
    patient_record: Optional[PatientRecordFullSchema] = Field(
        None, description="Patient record to delete"
    )
    empi: Optional[DeletePidFromEmpiRequest] = Field(
        None, description="EMPI records to delete"
    )


class DeletePIDResponseSchema(DeletePIDPreviewSchema):
    hash: str = Field(..., description="Hash of the record to delete")
    committed: bool = Field(..., description="Whether the deletion was committed")
