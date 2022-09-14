from typing import Optional

from pydantic import Field

from .base import OrmModel


class FacilitySchema(OrmModel):
    id: str = Field(..., description="Facility ID")
    description: Optional[str] = Field(None, description="Facility description")
