from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility, Patient, PatientRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.schemas.base import OrmModel

from .. import _assert_permission


class AgePoint(OrmModel):
    age: int
    count: int


class GenderPoint(OrmModel):
    gender: int
    count: int


class EthnicityPoint(OrmModel):
    ethnicity: Optional[str]
    count: int


class FacilityDemographicStats(OrmModel):
    age_dist: list[AgePoint]
    gender_dist: list[GenderPoint]
    ethnicity_dist: list[EthnicityPoint]


def get_facility_stats_demographics(
    ukrdc3: Session,
    facility_code: str,
    user: UKRDCUser,
) -> FacilityDemographicStats:
    """Extract demographic distributions for a given facility

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        FacilityDemographicStats: Facility demographic distribution statistics
    """
    # TODO: Consider caching the responses here, e.g. https://github.com/long2ice/fastapi-cache

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
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(Patient.gender)
    )

    gender_distribution = [
        GenderPoint(gender=row[0], count=row[1]) for row in q_genders
    ]
    gender_distribution.sort(key=lambda x: x.count, reverse=True)

    # Ethnicity distribution
    eth_count_func = func.count(Patient.ethnic_group_description)

    q_eth = (
        ukrdc3.query(Patient.ethnic_group_description, eth_count_func)
        .join(PatientRecord)
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(Patient.ethnic_group_description)
    )

    eth_distribution = [EthnicityPoint(ethnicity=row[0], count=row[1]) for row in q_eth]
    eth_distribution.sort(key=lambda x: x.count, reverse=True)

    # Composite
    return FacilityDemographicStats(
        age_dist=age_distribution,
        gender_dist=gender_distribution,
        ethnicity_dist=eth_distribution,
    )
