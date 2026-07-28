import datetime

from pydantic import Field

from ..base import OrmModel


class LabOrderShortSchema(OrmModel):
    """A short summary of a lab order"""

    id: str = Field(..., description="Lab order ID")
    pid: str = Field(..., description="Patient ID")

    entered_at_description: str | None = Field(
        None, description="Entered at facility description"
    )
    entered_at: str | None = Field(None, description="Entered at facility code")
    specimen_collected_time: datetime.datetime | None = Field(
        None, description="Specimen collected timestamp"
    )


class ResultItemSchema(OrmModel):
    """A single result item"""

    id: str = Field(..., description="Result ID")
    pid: str = Field(..., description="Patient ID")

    order_id: str = Field(..., description="Lab order ID")
    service_id: str = Field(..., description="Lab service ID")
    service_id_description: str | None = Field(
        None, description="Lab service description"
    )
    value: str | None = Field(None, description="Result value")
    value_units: str | None = Field(
        None, description="Result value units of measurement"
    )
    result_type: str | None = Field(None, description="Result type")
    pre_post: str | None = Field(None, description="Pre- or post- dialysis")
    observation_time: datetime.datetime | None = Field(
        None, description="Observation timestamp"
    )


class ResultItemServiceSchema(OrmModel):
    """Information about a single lab service"""

    id: str = Field(..., description="Lab service ID")
    description: str | None = Field(None, description="Lab service description")
    standard: str = Field(..., description="Lab service coding standard")


class LabOrderSchema(LabOrderShortSchema):
    """A lab order"""

    result_items: list[ResultItemSchema] = Field(
        ..., description="Result items for this lab order"
    )
