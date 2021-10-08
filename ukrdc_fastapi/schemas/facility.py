from typing import Optional

from .base import OrmModel


class FacilityMessageSummarySchema(OrmModel):
    total_IDs_count: Optional[int] = None
    success_IDs_count: Optional[int] = None
    error_IDs_count: Optional[int] = None
    error_IDs: Optional[list[str]] = None

    @classmethod
    def empty(cls):
        return cls(
            total_IDs_count=None,
            success_IDs_count=None,
            error_IDs_count=None,
            error_IDs=None,
        )


class FacilitySchema(OrmModel):
    id: str
    description: Optional[str]
