import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


class LabOrderShortSchema(OrmModel):
    """A short summary of a lab order"""

    id: str = Field(..., description="Lab order ID")
    pid: str = Field(..., description="Patient ID")

    entered_at_description: Optional[str] = Field(
        None, description="Entered at facility description"
    )
    entered_at: Optional[str] = Field(None, description="Entered at facility code")
    specimen_collected_time: Optional[datetime.datetime] = Field(
        None, description="Specimen collected timestamp"
    )


class ResultItemSchema(OrmModel):
    """A single result item"""

    id: str = Field(..., description="Result ID")
    pid: str = Field(..., description="Patient ID")

    order_id: str = Field(..., description="Lab order ID")
    service_id: str = Field(..., description="Lab service ID")
    service_id_description: Optional[str] = Field(
        None, description="Lab service description"
    )
    value: Optional[str] = Field(None, description="Result value")
    value_units: Optional[str] = Field(
        None, description="Result value units of measurement"
    )
    result_type: Optional[str] = Field(None, description="Result type")
    pre_post: Optional[str] = Field(None, description="Pre- or post- dialysis")
    observation_time: Optional[datetime.datetime] = Field(
        None, description="Observation timestamp"
    )


class ResultItemServiceSchema(OrmModel):
    """Information about a single lab service"""

    id: str = Field(..., description="Lab service ID")
    description: Optional[str] = Field(None, description="Lab service description")
    standard: str = Field(..., description="Lab service coding standard")


class LabOrderSchema(LabOrderShortSchema):
    """A lab order"""

    result_items: list[ResultItemSchema] = Field(
        ..., description="Result items for this lab order"
    )
