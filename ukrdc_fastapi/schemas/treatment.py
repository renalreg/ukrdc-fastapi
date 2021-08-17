import datetime
from typing import Optional

from .base import OrmModel


class TreatmentSchema(OrmModel):
    id: str

    from_time: Optional[datetime.date]
    to_time: Optional[datetime.date]

    admit_reason_code: Optional[str]
    admit_reason_code_std: Optional[str]
    admit_reason_desc: Optional[str]

    discharge_reason_code: Optional[str]
    discharge_reason_code_std: Optional[str]
    discharge_reason_desc: Optional[str]

    health_care_facility_code: Optional[str]
