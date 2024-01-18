import datetime
from typing import Optional

from pydantic import Field

from ukrdc_fastapi.schemas.base import OrmModel


class BaseDiagnosisSchema(OrmModel):
    """Base class for Diagnosis, RenalDiagnosis, and CauseOfDeath"""

    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: Optional[datetime.datetime] = Field(
        ..., description="Database update date"
    )

    enteredon: Optional[datetime.datetime] = Field(..., description="Entered date")
    updatedon: Optional[datetime.datetime] = Field(..., description="Updated date")

    diagnosistype: Optional[str] = Field(..., description="Diagnosis type")

    diagnosis_code: Optional[str] = Field(None, description="Diagnosis code")
    diagnosis_code_std: Optional[str] = Field(
        None, description="Diagnosis code standard"
    )
    diagnosis_desc: Optional[str] = Field(None, description="Diagnosis description")

    comments: Optional[str] = Field(None, description="Diagnosis comments")


class DiagnosisSchema(BaseDiagnosisSchema):
    """A diagnosis record."""

    id: str = Field(..., description="Diagnosis ID")

    identification_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis onset timestamp"
    )


class RenalDiagnosisSchema(BaseDiagnosisSchema):
    """A renal diagnosis record."""

    identification_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis onset timestamp"
    )


class CauseOfDeathSchema(BaseDiagnosisSchema):
    """A cause of death record."""

    pass
