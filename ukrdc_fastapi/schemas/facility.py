from typing import Optional

from .base import OrmModel


class FacilitySchema(OrmModel):
    id: str
    description: Optional[str]
