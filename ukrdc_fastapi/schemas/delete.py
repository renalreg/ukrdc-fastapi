from typing import Optional

from ukrdc_fastapi.schemas.empi import (
    LinkRecordSummarySchema,
    MasterRecordSchema,
    PersonSchema,
    PidXRefSchema,
    WorkItemSummarySchema,
)
from ukrdc_fastapi.schemas.patientrecord import PatientRecordFullSchema

from .base import OrmModel


class DeletePIDRequestSchema(OrmModel):
    hash: Optional[str]
    delete_from_empi: bool = True


class DeletePIDFromEMPISchema(OrmModel):
    persons: list[PersonSchema]
    master_records: list[MasterRecordSchema]
    pidxrefs: list[PidXRefSchema]
    work_items: list[WorkItemSummarySchema]
    link_records: list[LinkRecordSummarySchema]


class DeletePIDPreviewSchema(OrmModel):
    patient_record: Optional[PatientRecordFullSchema]
    empi: Optional[DeletePIDFromEMPISchema]


class DeletePIDResponseSchema(DeletePIDPreviewSchema):
    hash: str
