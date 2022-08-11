from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy import and_, extract, func
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Code, Facility, Patient, PatientRecord

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
    eth_count_func = func.count("*")

    # Count distinct combinations of ethnicity code and free-text ethnicity description
    # Produces tuples of the form (ethnic_group_code, ethnic_group_description (free-text), count)
    q_eth_1 = (
        ukrdc3.query(
            Patient.ethnic_group_code, Patient.ethnic_group_description, eth_count_func
        )
        .join(PatientRecord)
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(
            Patient.ethnic_group_code,
            Patient.ethnic_group_description,
        )
    ).subquery()

    # Fetch code descriptions for ethnicity codes
    # Produces tuples of the form (ethnic_group_code, ethnic_group_description (free-text), count, ethnic_group_code.description (NHS_DATA_DICTIONARY))
    q_eth_2 = ukrdc3.query(q_eth_1, Code.description).join(
        Code,
        and_(
            Code.coding_standard == "NHS_DATA_DICTIONARY",
            q_eth_1.c.ethnic_group_code == Code.code,
        ),
        isouter=True,
    )

    eth_counts_dict: dict[str, int] = {}

    for row in q_eth_2:
        # Preferably use Codes.code for the ethnicity label, otherwise use the free-text description,
        # otherwise assume it's unknown
        ethnicity: str = row[3] or row[1] or "Unknown"
        # Catch the case where we've already seen this code. This could occur if the site sends an
        # ethnicity code AND a free-text description
        if ethnicity in eth_counts_dict:
            eth_counts_dict[ethnicity] += row[2]
        else:
            eth_counts_dict[ethnicity] = row[2]

    eth_distribution = [
        EthnicityPoint(ethnicity=key, count=count)
        for key, count in eth_counts_dict.items()
    ]
    eth_distribution.sort(key=lambda x: x.count, reverse=True)

    # Composite
    return FacilityDemographicStats(
        age_dist=age_distribution,
        gender_dist=gender_distribution,
        ethnicity_dist=eth_distribution,
    )
