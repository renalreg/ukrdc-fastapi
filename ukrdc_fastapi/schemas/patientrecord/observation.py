import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


class ObservationSchema(OrmModel):
    """Information about a single observation"""

    observation_code: str = Field(..., description="The observation type code")
    observation_code_std: str = Field(
        ..., description="The observation type code standard"
    )

    observation_time: datetime.datetime = Field(
        ..., description="Observation timestamp"
    )
    observation_desc: Optional[str] = Field(None, description="Observation description")
    observation_value: Optional[str] = Field(None, description="Observation value")
    observation_units: Optional[str] = Field(
        None, description="Observation units of measurement"
    )
    pre_post: Optional[str] = Field(None, description="Pre- or post- dialysis")
    entered_at: Optional[str] = Field(None, description="Entered at facility code")
    entered_at_description: Optional[str] = Field(
        None, description="Entered at facility description"
    )
