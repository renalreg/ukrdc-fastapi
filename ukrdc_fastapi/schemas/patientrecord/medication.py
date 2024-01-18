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
    comment: Optional[str] = Field(None, description="Comment on the medication")
    entering_organization_code: Optional[str] = Field(
        None, description="Code of the organization that entered the medication"
    )
    entering_organization_description: Optional[str] = Field(
        None, description="Description of the organization that entered the medication"
    )
