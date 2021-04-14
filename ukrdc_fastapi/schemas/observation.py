import datetime
from typing import Optional

from .base import OrmModel


class ObservationSchema(OrmModel):
    observation_time: datetime.datetime
    observation_desc: Optional[str]
    observation_value: str
    observation_units: Optional[str]
    pre_post: Optional[str]
    entered_at: Optional[str]
    entered_at_description: Optional[str]
