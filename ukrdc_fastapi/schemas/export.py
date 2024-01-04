from pydantic import Field

from .base import OrmModel


class ExportResponseSchema(OrmModel):
    """Response to a record export call"""

    status: str = Field(..., description="Response status of the export")
    number_of_messages: int = Field(
        ..., description="Number of messages sent in the export request"
    )
