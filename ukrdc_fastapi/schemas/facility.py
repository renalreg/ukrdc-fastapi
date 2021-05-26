from typing import Optional

from pydantic import BaseModel


class FacilitySchema(BaseModel):
    id: str
    description: Optional[str]
