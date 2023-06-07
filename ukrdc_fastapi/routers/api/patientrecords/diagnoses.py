from typing import Optional
from pydantic import Field
from sqlalchemy import and_
from ukrdc_fastapi.schemas.patientrecord import (
    DiagnosisSchema,
    RenalDiagnosisSchema,
    CauseOfDeathSchema,
)

from fastapi import APIRouter, Depends, Security
from ukrdc_sqla.ukrdc import (
    PatientRecord,
    Diagnosis,
    RenalDiagnosis,
    CauseOfDeath,
    Code,
)

from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    RecordOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from .dependencies import _get_patientrecord

router = APIRouter()

# Extended schemas which will include descriptions obtained by looking up codes in the code_list table


class ExtendedDiagnosisSchema(DiagnosisSchema):
    description: Optional[str] = Field(
        None, description="Formal coding description, if available"
    )


class ExtendedRenalDiagnosisSchema(RenalDiagnosisSchema):
    description: Optional[str] = Field(
        None, description="Formal coding description, if available"
    )


class ExtendedCauseOfDeathSchema(CauseOfDeathSchema):
    description: Optional[str] = Field(
        None, description="Formal coding description, if available"
    )


@router.get(
    "/diagnosis",
    response_model=list[ExtendedDiagnosisSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_diagnosis(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's diagnoses"""

    q = (
        patient_record.diagnoses.outerjoin(
            Code,
            and_(
                Code.coding_standard == Diagnosis.diagnosiscodestd,
                Code.code == Diagnosis.diagnosiscode,
            ),
        )
        .with_entities(Diagnosis, Code.description)
        .order_by(Diagnosis.creation_date.desc())
    )

    items = []

    for row in q:
        item = ExtendedDiagnosisSchema.from_orm(row[0])
        item.description = row[1]
        items.append(item)

    audit.add_event(
        Resource.DIAGNOSES,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return items


@router.get(
    "/renaldiagnosis",
    response_model=list[ExtendedRenalDiagnosisSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_renal_diagnosis(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's renal diagnoses"""
    q = (
        patient_record.renaldiagnoses.join(
            Code,
            and_(
                Code.coding_standard == RenalDiagnosis.diagnosiscodestd,
                Code.code == RenalDiagnosis.diagnosiscode,
            ),
        )
        .with_entities(RenalDiagnosis, Code.description)
        .order_by(RenalDiagnosis.creation_date.desc())
    )

    items = []

    for row in q:
        item = ExtendedRenalDiagnosisSchema.from_orm(row[0])
        item.description = row[1]
        items.append(item)

    audit.add_event(
        Resource.RENALDIAGNOSES,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return items


@router.get(
    "/causeofdeath",
    response_model=list[ExtendedCauseOfDeathSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_cause_of_death(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a specific patient's cause of death"""
    q = (
        patient_record.cause_of_death.join(
            Code,
            and_(
                Code.coding_standard == CauseOfDeath.diagnosiscodestd,
                Code.code == CauseOfDeath.diagnosiscode,
            ),
        )
        .with_entities(CauseOfDeath, Code.description)
        .order_by(CauseOfDeath.creation_date.desc())
    )

    items = []

    for row in q:
        item = ExtendedCauseOfDeathSchema.from_orm(row[0])
        item.description = row[1]
        items.append(item)

    audit.add_event(
        Resource.CAUSEOFDEATH,
        None,
        RecordOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.READ
        ),
    )

    return items
