import datetime
from typing import Optional

from .base import OrmModel


class MedicationSchema(OrmModel):
    from_time: Optional[datetime.datetime]
    to_time: Optional[datetime.datetime]
    drug_product_generic: str
    comment: Optional[str]
    entering_organization_code: Optional[str]
    entering_organization_description: Optional[str]
