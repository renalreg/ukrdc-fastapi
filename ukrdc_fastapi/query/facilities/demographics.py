from typing import Optional

from fastapi.exceptions import HTTPException
from pydantic import Field
from sqlalchemy import and_, extract, func
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Code, Facility, Patient, PatientRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.schemas.base import OrmModel

from . import _assert_permission


class AgePoint(OrmModel):
    """Histogram point for age distribution"""

    age: int = Field(..., description="Age in years (x-axis)")
    count: int = Field(..., description="Number of patients (y-axis)")


class GenderPoint(OrmModel):
    """Histogram point for gender distribution"""

    gender: int = Field(..., description="Gender code (x-axis)")
    count: int = Field(..., description="Number of patients (y-axis)")


class EthnicityPoint(OrmModel):
    """Histogram point for ethnicity distribution"""

    ethnicity: Optional[str] = Field(..., description="Ethnicity code (x-axis)")
    count: int = Field(..., description="Number of patients (y-axis)")


class FacilityDemographicStats(OrmModel):
    """Basic demographic statistics for a facility"""

    age_dist: list[AgePoint] = Field(..., description="Age distribution")
    gender_dist: list[GenderPoint] = Field(..., description="Gender code distribution")
    ethnicity_dist: list[EthnicityPoint] = Field(
        ..., description="Ethnicity code distribution"
    )


def get_facility_demographics(
    ukrdc3: Session,
    facility_code: str,
    user: UKRDCUser,
) -> FacilityDemographicStats:
    """Extract demographic distributions for all UKRDC/RDA records in a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        FacilityDemographicStats: Facility demographic distribution statistics
    """
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise HTTPException(404, detail="Facility not found")

    # Assert permissions
    _assert_permission(facility, user)

    # Age distribution
    age_func = extract("year", func.age(Patient.birth_time))
    age_count_func = func.count(age_func)

    q_ages = (
        ukrdc3.query(age_func, age_count_func)
        .join(PatientRecord)
        .filter(PatientRecord.sendingextract == "UKRDC")
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(age_func)
        .order_by(age_func)
    )

    age_distribution = [AgePoint(age=int(row[0]), count=row[1]) for row in q_ages]

    # Gender distribution
    gender_count_func = func.count(Patient.gender)

    q_genders = (
        ukrdc3.query(Patient.gender, gender_count_func)
        .join(PatientRecord)
        .filter(PatientRecord.sendingextract == "UKRDC")
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(Patient.gender)
    )

    gender_distribution = [
        GenderPoint(gender=row[0], count=row[1]) for row in q_genders
    ]
    gender_distribution.sort(key=lambda x: x.count, reverse=True)

    # Ethnicity distribution
    eth_count_func = func.count("*")

    # Count distinct combinations of ethnicity code and free-text ethnicity description
    # Produces tuples of the form (ethnic_group_code,  count)
    q_eth_1 = (
        ukrdc3.query(Patient.ethnic_group_code, eth_count_func)
        .join(PatientRecord)
        .filter(PatientRecord.sendingextract == "UKRDC")
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(Patient.ethnic_group_code)
    ).subquery()

    # Fetch code descriptions for ethnicity codes
    # Produces tuples of the form (ethnic_group_code, count, ethnic_group_code.description (NHS_DATA_DICTIONARY))
    q_eth_2 = ukrdc3.query(q_eth_1, Code.description).join(
        Code,
        and_(
            Code.coding_standard == "NHS_DATA_DICTIONARY",
            q_eth_1.c.ethnic_group_code == Code.code,
        ),
        isouter=True,
    )

    eth_distribution = [
        EthnicityPoint(ethnicity=row[2], count=row[1]) for row in q_eth_2
    ]
    eth_distribution.sort(key=lambda x: x.count, reverse=True)

    # Composite
    return FacilityDemographicStats(
        age_dist=age_distribution,
        gender_dist=gender_distribution,
        ethnicity_dist=eth_distribution,
    )
