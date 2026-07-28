import datetime
from typing import Optional, Annotated

from pydantic import Field, BeforeValidator

from ..base import OrmModel


class MedicationSchema(OrmModel):
    """Information about a single medication"""

    from_time: datetime.datetime | None = Field(
        None, description="Time the patient started taking the medication"
    )
    to_time: datetime.datetime | None = Field(
        None, description="Time the patient stopped taking the medication"
    )

    drug_product_generic: str = Field(..., description="Generic name of the medication")

    dosequantity: Annotated[
        str | None, BeforeValidator(lambda v: str(v) if v is not None else v)
    ] = Field(None, description="...")
    doseuomcode: str | None = Field(None, description="Dose unit of measurement code")
    doseuomcodestd: str | None = Field(
        None, description="Dose unit of measurement coding standard"
    )
    doseuomdesc: str | None = Field(
        None, description="Dose unit of measurement description"
    )

    frequency: str | None = Field(None, description="Medication frequency")

    routecode: str | None = Field(None, description="Route code")
    routecodestd: str | None = Field(None, description="Route coding standard")
    routedesc: str | None = Field(None, description="Route description")

    comment: str | None = Field(None, description="Comment on the medication")

    entering_organization_code: str | None = Field(
        None, description="Code of the organization that entered the medication"
    )
    entering_organization_description: str | None = Field(
        None, description="Description of the organization that entered the medication"
    )
