import datetime
from typing import Optional

from fastapi_hypermodel.hypermodel import LinkSet, UrlFor

from .base import OrmModel


class CodeSchema(OrmModel):
    coding_standard: str
    code: str
    description: Optional[str]
    object_type: Optional[str]

    creation_date: datetime.datetime
    update_date: Optional[datetime.datetime]

    units: Optional[str]

    links = LinkSet(
        {
            "self": UrlFor(
                "code_details",
                {"coding_standard": "<coding_standard>", "code": "<code>"},
            )
        }
    )


class CodeMapSchema(OrmModel):
    source_coding_standard: str
    source_code: str

    destination_coding_standard: str
    destination_code: str

    creation_date: datetime.datetime
    update_date: Optional[datetime.datetime]
