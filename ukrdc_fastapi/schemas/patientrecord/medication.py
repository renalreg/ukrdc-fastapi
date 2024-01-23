import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


class MedicationSchema(OrmModel):
    """Information about a single medication"""

    from_time: Optional[datetime.datetime] = Field(
        None, description="Time the patient started taking the medication"
    )
    to_time: Optional[datetime.datetime] = Field(
        None, description="Time the patient stopped taking the medication"
    )

    drug_product_generic: str = Field(..., description="Generic name of the medication")

    doseuomcode: Optional[str] = Field(
        None, description="Dose unit of measurement code"
    )
    doseuomcodestd: Optional[str] = Field(
        None, description="Dose unit of measurement coding standard"
    )
    doseuomdesc: Optional[str] = Field(
        None, description="Dose unit of measurement description"
    )

    routecode: Optional[str] = Field(None, description="Route code")
    routecodestd: Optional[str] = Field(None, description="Route coding standard")
    routedesc: Optional[str] = Field(None, description="Route description")

    frequency: Optional[str] = Field(None, description="Medication frequency")

    comment: Optional[str] = Field(None, description="Comment on the medication")

    entering_organization_code: Optional[str] = Field(
        None, description="Code of the organization that entered the medication"
    )
    entering_organization_description: Optional[str] = Field(
        None, description="Description of the organization that entered the medication"
    )
