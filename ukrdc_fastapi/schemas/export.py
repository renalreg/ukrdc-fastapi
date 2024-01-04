from pydantic import Field

from .base import OrmModel


class ExportResponseSchema(OrmModel):
    """Response to a record export call"""

    status: str = Field(..., description="Response status of the message")
    number_of_messages: int = Field(
        None, description="Number of messages sent in the export request"
    )
