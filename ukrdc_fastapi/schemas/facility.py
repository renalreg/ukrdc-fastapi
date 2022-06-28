from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor

from .base import OrmModel


class FacilitySchema(OrmModel):
    id: str
    description: Optional[str]

    links = LinkSet(
        {
            "self": UrlFor("facility", {"code": "<id>"}),
            "errorsHistory": UrlFor("facility_errrors_history", {"code": "<id>"}),
            "patientsLatestErrors": UrlFor(
                "facility_patients_latest_errors", {"code": "<id>"}
            ),
            "stats": LinkSet(
                {
                    "demographics": UrlFor(
                        "facility_stats_demographics", {"code": "<id>"}
                    ),
                }
            ),
        }
    )
