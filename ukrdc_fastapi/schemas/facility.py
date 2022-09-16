from typing import Optional

from pydantic import Field

from .base import OrmModel


class FacilitySchema(OrmModel):
    """Information about a single facility"""

    id: str = Field(..., description="Facility ID")
    description: Optional[str] = Field(None, description="Facility description")
