import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility
from ukrdc_stats.calculators.demographics import (
    DemographicsStats,
    DemographicStatsCalculator,
)
from ukrdc_stats.calculators.krt import (
    KRTStatsCalculator,
    UnitLevelKRTStats,
)

from ukrdc_fastapi.exceptions import MissingFacilityError


def get_facility_demographic_stats(
    ukrdc3: Session,
    facility_code: str,
) -> DemographicsStats:
    """Extract demographic distributions for all UKRDC/RDA records in a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

    Returns:
        FacilityDemographicStats: Facility demographic distribution statistics
    """
    # Assert the facility exists
    stmt = select(Facility).where(Facility.code == facility_code)
    facility = ukrdc3.scalars(stmt).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # Calculate all demographic stats
    return DemographicStatsCalculator(ukrdc3, facility.code).extract_stats()  #  type:ignore


def get_facility_dialysis_stats(
    ukrdc3: Session,
    facility_code: str,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> UnitLevelKRTStats:
    """Extract dialysis statistics for all UKRDC/RDA records in a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        since (datetime.datetime, optional): Date from which to extract dialysis statistics/ from time
        until (datetime.datetime, optional): Date from which to extract dialysis statistics/ to time
    Returns:
        DialysisStats: Facility demographic distribution statistics
    """
    # Assert the facility exists
    stmt = select(Facility).where(Facility.code == facility_code)
    facility = ukrdc3.scalars(stmt).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # Handle default arguments
    from_time: datetime.datetime = (
        since or datetime.datetime.now() - datetime.timedelta(days=90)
    )
    to_time: datetime.datetime = until or datetime.datetime.now()

    # Calculate all demographic stats
    return KRTStatsCalculator(
        ukrdc3,  # type:ignore
        facility.code,  # type:ignore
        from_time=from_time,  # type:ignore
        to_time=to_time,  # type:ignore
    ).extract_stats()
