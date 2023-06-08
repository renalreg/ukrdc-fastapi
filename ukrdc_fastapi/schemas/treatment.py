import datetime
from typing import Optional

from pydantic import Field

from .base import OrmModel


class TreatmentSchema(OrmModel):
    """A treatment record"""

    id: str = Field(..., description="Treatment ID")

    from_time: Optional[datetime.date] = Field(None, description="Treatment start date")
    to_time: Optional[datetime.date] = Field(None, description="Treatment end date")

    # Admit reason
    admit_reason_code: Optional[str] = Field(
        None, description="Treatment admission reason code"
    )
    admit_reason_code_std: Optional[str] = Field(
        None, description="Treatment admission reason code standard"
    )
    admit_reason_desc: Optional[str] = Field(
        None, description="Treatment admission reason description"
    )

    # Discharge reason
    discharge_reason_code: Optional[str] = Field(
        None, description="Treatment discharge reason code"
    )
    discharge_reason_code_std: Optional[str] = Field(
        None, description="Treatment discharge reason code standard"
    )
    discharge_reason_desc: Optional[str] = Field(
        None, description="Treatment discharge reason description"
    )

    # Discharge location
    discharge_location_code: Optional[str] = Field(
        None, description="Treatment discharge location code"
    )
    discharge_location_code_std: Optional[str] = Field(
        None, description="Treatment discharge location code standard"
    )
    discharge_location_desc: Optional[str] = Field(
        None, description="Treatment discharge location description"
    )

    # Health care facility
    health_care_facility_code: Optional[str] = Field(
        None, description="Treatment health care facility code"
    )
    health_care_facility_code_std: Optional[str] = Field(
        None, description="Treatment health care facility code standard"
    )
    health_care_facility_desc: Optional[str] = Field(
        None, description="Treatment health care facility description"
    )

    # Attributes
    qbl05: Optional[str]
