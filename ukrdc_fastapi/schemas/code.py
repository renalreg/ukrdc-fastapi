import datetime
from typing import Optional

from pydantic import Field

from .base import OrmModel


class CodeSchema(OrmModel):
    """Infomration about a single standard code"""

    coding_standard: str = Field(..., description="Coding standard")
    code: str = Field(..., description="Code")
    description: Optional[str] = Field(None, description="Code description")
    object_type: Optional[str] = Field(
        None,
        description="Object type, e.g. observation, result, dose_unit. Rarely used in practice.",
    )

    creation_date: datetime.datetime = Field(..., description="Creation date")
    update_date: Optional[datetime.datetime] = Field(..., description="Update date")

    units: Optional[str] = Field(None, description="Units o fmeasurement")


class CodeMapSchema(OrmModel):
    """Infomration about a mapping between two codes"""

    source_coding_standard: str = Field(..., description="Source coding standard")
    source_code: str = Field(..., description="Source code")

    destination_coding_standard: str = Field(
        ..., description="Destination coding standard"
    )
    destination_code: str = Field(..., description="Destination code")

    creation_date: datetime.datetime = Field(..., description="Creation date")
    update_date: Optional[datetime.datetime] = Field(..., description="Update date")


class CodeExclusionSchema(OrmModel):
    """Infomration about a code exclusion from a particular internal system"""

    coding_standard: str = Field(..., description="Coding standard")
    code: str = Field(..., description="Code")
    system: str = Field(..., description="System to exclude the code from")
