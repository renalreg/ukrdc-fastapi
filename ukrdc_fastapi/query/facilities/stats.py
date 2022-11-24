from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility
from ukrdc_stats.calculators.demographics import (
    DemographicsStats,
    DemographicStatsCalculator,
)

from ukrdc_fastapi.dependencies.auth import UKRDCUser

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
        raise HTTPException(404, detail="Facility not found")

    # Assert permissions
    _assert_permission(facility, user)

    # Calculate all demographic stats
    return DemographicStatsCalculator(ukrdc3, facility.code).extract_stats()
