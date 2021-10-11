from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor

from ukrdc_fastapi.schemas.message import MessageSchema

from .base import OrmModel


class FacilityMessageSummarySchema(OrmModel):
    total_IDs_count: Optional[int] = None
    success_IDs_count: Optional[int] = None
    error_IDs_count: Optional[int] = None

    error_IDs_messages: Optional[list[MessageSchema]] = None

    @classmethod
    def empty(cls):
        """
        Build an empty FacilityMessageSummarySchema object
        """
        return cls(
            total_IDs_count=None,
            success_IDs_count=None,
            error_IDs_count=None,
            error_IDs=None,
        )


class FacilitySchema(OrmModel):
    id: str
    description: Optional[str]

    links = LinkSet(
        {
            "self": UrlFor("facility", {"code": "<id>"}),
            "errorsHistory": UrlFor("facility_errrors_history", {"code": "<id>"}),
        }
    )
