import datetime

from .base import OrmModel


class MedicationSchema(OrmModel):
    from_time: datetime.datetime
    to_time: datetime.datetime
    drug_product_generic: str
    comment: str
    entering_organization_code: str
    entering_organization_description: str
