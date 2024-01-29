import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility
from ukrdc_stats.calculators.demographics import (
    DemographicsStats,
    DemographicStatsCalculator,
)
from ukrdc_stats.calculators.dialysis import (
    DialysisStatsCalculator,
    UnitLevelDialysisStats,
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
    return DemographicStatsCalculator(ukrdc3, facility.code).extract_stats()


def get_facility_dialysis_stats(
    ukrdc3: Session,
    facility_code: str,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> UnitLevelDialysisStats:
    """Extract dialysis statistics for all UKRDC/RDA records in a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

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
    return DialysisStatsCalculator(
        ukrdc3, facility.code, from_time=from_time, to_time=to_time
    ).extract_stats()
