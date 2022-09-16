import datetime
from typing import Optional

from pydantic import Field

from .base import OrmModel


class TreatmentSchema(OrmModel):
    """A treatment record"""

    id: str = Field(..., description="Treatment ID")

    from_time: Optional[datetime.date] = Field(None, description="Treatment start date")
    to_time: Optional[datetime.date] = Field(None, description="Treatment end date")

    admit_reason_code: Optional[str] = Field(
        None, description="Treatment admission reason code"
    )
    admit_reason_code_std: Optional[str] = Field(
        None, description="Treatment admission reason code standard"
    )
    admit_reason_desc: Optional[str] = Field(
        None, description="Treatment admission reason description"
    )

    discharge_reason_code: Optional[str] = Field(
        None, description="Treatment discharge reason code"
    )
    discharge_reason_code_std: Optional[str] = Field(
        None, description="Treatment discharge reason code standard"
    )
    discharge_reason_desc: Optional[str] = Field(
        None, description="Treatment discharge reason description"
    )

    health_care_facility_code: Optional[str] = Field(
        None, description="Treatment health care facility code"
    )
