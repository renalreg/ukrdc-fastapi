from ukrdc_fastapi.query.patientrecords.diagnoses import (
    ExtendedCauseOfDeathSchema,
    ExtendedDiagnosisSchema,
    ExtendedRenalDiagnosisSchema,
    get_patient_cause_of_death,
    get_patient_diagnosis,
    get_patient_renal_diagnosis,
)

from fastapi import APIRouter, Depends, Security
from ukrdc_sqla.ukrdc import (
    PatientRecord,
)

from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from .dependencies import _get_patientrecord

router = APIRouter()

# Extended schemas which will include descriptions obtained by looking up codes in the code_list table


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

    audit.add_event(
        Resource.DIAGNOSES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return get_patient_diagnosis(patient_record)


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
    audit.add_event(
        Resource.RENALDIAGNOSES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return get_patient_renal_diagnosis(patient_record)


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

    audit.add_event(
        Resource.CAUSEOFDEATH,
        None,
        AuditOperation.READ,
        parent=audit.add_event(
            Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.READ
        ),
    )

    return get_patient_cause_of_death(patient_record)
