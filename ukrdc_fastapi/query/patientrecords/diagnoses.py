from typing import Optional
from pydantic import Field
from sqlalchemy import and_
from ukrdc_fastapi.schemas.patientrecord import (
    DiagnosisSchema,
    RenalDiagnosisSchema,
    CauseOfDeathSchema,
)

from ukrdc_sqla.ukrdc import (
    PatientRecord,
    Diagnosis,
    RenalDiagnosis,
    CauseOfDeath,
    Code,
)

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


def get_patient_diagnosis(
    patient_record: PatientRecord,
) -> list[ExtendedDiagnosisSchema]:
    """Retreive a specific patient's diagnoses, including coding lookups"""

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

    return items


def get_patient_renal_diagnosis(
    patient_record: PatientRecord,
) -> list[ExtendedRenalDiagnosisSchema]:
    """Retreive a specific patient's renal diagnoses, including coding lookups"""
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

    return items


def get_patient_cause_of_death(
    patient_record: PatientRecord,
) -> list[ExtendedCauseOfDeathSchema]:
    """Retreive a specific patient's cause of death, including coding lookups"""
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

    return items
