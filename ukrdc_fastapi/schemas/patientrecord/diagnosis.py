import datetime

from pydantic import Field

from ukrdc_fastapi.schemas.base import OrmModel


class BaseDiagnosisSchema(OrmModel):
    """Base class for Diagnosis, RenalDiagnosis, and CauseOfDeath"""

    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: datetime.datetime | None = Field(
        ..., description="Database update date"
    )

    enteredon: datetime.datetime | None = Field(..., description="Entered date")
    updatedon: datetime.datetime | None = Field(..., description="Updated date")

    diagnosistype: str | None = Field(..., description="Diagnosis type")

    diagnosis_code: str | None = Field(None, description="Diagnosis code")
    diagnosis_code_std: str | None = Field(None, description="Diagnosis code standard")
    diagnosis_desc: str | None = Field(None, description="Diagnosis description")

    comments: str | None = Field(None, description="Diagnosis comments")


class DiagnosisSchema(BaseDiagnosisSchema):
    """A diagnosis record."""

    id: str = Field(..., description="Diagnosis ID")

    identification_time: datetime.datetime | None = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: datetime.datetime | None = Field(
        None, description="Diagnosis onset timestamp"
    )


class RenalDiagnosisSchema(BaseDiagnosisSchema):
    """A renal diagnosis record."""

    identification_time: datetime.datetime | None = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: datetime.datetime | None = Field(
        None, description="Diagnosis onset timestamp"
    )


class CauseOfDeathSchema(BaseDiagnosisSchema):
    """A cause of death record."""

    pass
