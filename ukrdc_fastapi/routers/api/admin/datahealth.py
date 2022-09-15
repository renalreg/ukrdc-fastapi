import datetime

from fastapi import APIRouter, Depends, Security
from pydantic import Field
from sqlalchemy.orm import Session
from ukrdc_sqla.stats import LastRunTimes

from ukrdc_fastapi.dependencies import get_jtrace, get_statsdb
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.stats import MultipleUKRDCIDGroup, get_multiple_ukrdcids
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.utils.paginate import Page, paginate_sequence

router = APIRouter(tags=["Admin/Data Health"])

DATA_HEALTH_PERMISSIONS = [
    Permissions.READ_RECORDS,
    Permissions.UNIT_ALL,
]


class LastRunTime(OrmModel):
    """Information about the last time a data health check was run"""

    last_run_time: datetime.datetime = Field(
        ..., description="Timestamp of last time the results were recalculated"
    )


@router.get(
    "/multiple_ukrdcids",
    response_model=Page[MultipleUKRDCIDGroup],
    dependencies=[Security(auth.permission(DATA_HEALTH_PERMISSIONS))],
)
def datahealth_multiple_ukrdcids(
    jtrace: Session = Depends(get_jtrace),
    statsdb: Session = Depends(get_statsdb),
):
    """Retreive list of patients with multiple UKRDC IDs"""
    return paginate_sequence(get_multiple_ukrdcids(statsdb, jtrace))


@router.get(
    "/multiple_ukrdcids/last_run",
    response_model=LastRunTime,
    dependencies=[Security(auth.permission(DATA_HEALTH_PERMISSIONS))],
)
def datahealth_multiple_ukrdcids_last_run(
    statsdb: Session = Depends(get_statsdb),
):
    """Retreive the datetime the multiple_ukrdcid table was fully refreshed"""
    return statsdb.query(LastRunTimes).get(("multiple_ukrdcid", ""))
