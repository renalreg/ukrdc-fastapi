import datetime
from typing import Optional

from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility
from ukrdc_stats.calculators.demographics import (
    DemographicsStats,
    DemographicStatsCalculator,
)
from ukrdc_stats.calculators.dialysis import DialysisStats, DialysisStatsCalculator

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.exceptions import MissingFacilityError

from . import _assert_permission


def get_facility_demographic_stats(
    ukrdc3: Session,
    facility_code: str,
    user: UKRDCUser,
) -> DemographicsStats:
    """Extract demographic distributions for all UKRDC/RDA records in a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        FacilityDemographicStats: Facility demographic distribution statistics
    """
    # Assert the facility exists
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # Assert permissions
    _assert_permission(facility, user)

    # Calculate all demographic stats
    return DemographicStatsCalculator(ukrdc3, facility.code).extract_stats()


def get_facility_dialysis_stats(
    ukrdc3: Session,
    facility_code: str,
    user: UKRDCUser,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> DialysisStats:
    """Extract dialysis statistics for all UKRDC/RDA records in a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        DialysisStats: Facility demographic distribution statistics
    """
    # Assert the facility exists
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # Assert permissions
    _assert_permission(facility, user)

    # Handle default arguments
    from_time: datetime.datetime = (
        since or datetime.datetime.now() - datetime.timedelta(days=90)
    )
    to_time: datetime.datetime = until or datetime.datetime.now()

    # Calculate all demographic stats
    return DialysisStatsCalculator(
        ukrdc3, facility.code, from_time=from_time, to_time=to_time
    ).extract_stats()
