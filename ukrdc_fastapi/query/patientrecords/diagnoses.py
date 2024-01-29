from typing import Optional
from pydantic import Field
from sqlalchemy import and_, select
from ukrdc_fastapi.schemas.patientrecord import (
    DiagnosisSchema,
    RenalDiagnosisSchema,
    CauseOfDeathSchema,
)
from sqlalchemy.orm import Session
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
    ukrdc3: Session,
) -> list[ExtendedDiagnosisSchema]:
    """Retreive a specific patient's diagnoses, including coding lookups"""

    stmt = (
        select(Diagnosis, Code.description)
        .outerjoin(
            Code,
            and_(
                Code.coding_standard == Diagnosis.diagnosiscodestd,
                Code.code == Diagnosis.diagnosiscode,
            ),
        )
        .where(Diagnosis.pid == patient_record.pid)
        .order_by(Diagnosis.creation_date.desc())
    )

    result = ukrdc3.execute(stmt)

    items = []

    for row in result:
        item = ExtendedDiagnosisSchema.from_orm(row[0])
        item.description = row[1]
        items.append(item)

    return items


def get_patient_renal_diagnosis(
    patient_record: PatientRecord,
    ukrdc3: Session,
) -> list[ExtendedRenalDiagnosisSchema]:
    """Retreive a specific patient's renal diagnoses, including coding lookups"""

    stmt = (
        select(RenalDiagnosis, Code.description)
        .outerjoin(
            Code,
            and_(
                Code.coding_standard == RenalDiagnosis.diagnosiscodestd,
                Code.code == RenalDiagnosis.diagnosiscode,
            ),
        )
        .where(RenalDiagnosis.pid == patient_record.pid)
        .order_by(RenalDiagnosis.creation_date.desc())
    )

    result = ukrdc3.execute(stmt)

    items = []

    for row in result:
        item = ExtendedRenalDiagnosisSchema.from_orm(row.RenalDiagnosis)
        item.description = row.description
        items.append(item)

    return items


def get_patient_cause_of_death(
    patient_record: PatientRecord,
    ukrdc3: Session,
) -> list[ExtendedCauseOfDeathSchema]:
    """Retrieve a specific patient's cause of death, including coding lookups"""

    stmt = (
        select(CauseOfDeath, Code.description)
        .outerjoin(
            Code,
            and_(
                Code.coding_standard == CauseOfDeath.diagnosiscodestd,
                Code.code == CauseOfDeath.diagnosiscode,
            ),
        )
        .where(CauseOfDeath.pid == patient_record.pid)
        .order_by(CauseOfDeath.creation_date.desc())
    )

    result = ukrdc3.execute(stmt)

    items = []

    for row in result:
        item = ExtendedCauseOfDeathSchema.from_orm(row.CauseOfDeath)
        item.description = row.description
        items.append(item)

    return items
