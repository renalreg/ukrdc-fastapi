import datetime
from typing import Optional

from .base import OrmModel


class TreatmentSchema(OrmModel):
    id: str
    pid: str

    from_time: Optional[datetime.date]
    to_time: Optional[datetime.date]

    admit_reason_code: Optional[str]
    admission_source_code_std: Optional[str]

    health_care_facility_code: Optional[str]
    health_care_facility_code_std: Optional[str]
