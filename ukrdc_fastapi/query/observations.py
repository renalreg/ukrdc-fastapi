from typing import Optional

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.ukrdc import Observation, PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


def get_observations(
    ukrdc3: Session,
    user: UKRDCUser,
    pid: Optional[str] = None,
    codes: Optional[list[str]] = None,
    sort_query: bool = True,
) -> Query:
    """Get a list of Patient observations

    Args:
        ukrdc3 (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object
        pid (Optional[str], optional): PID of observation patientrecord. Defaults to None.
        codes (Optional[list[str]], optional): List of observation codes to filter by. Defaults to None.

    Returns:
        Query: SQLALchemy query
    """
    observations = ukrdc3.query(Observation)

    if pid:
        observations = observations.filter(Observation.pid == pid)

    if codes:
        observations = observations.filter(Observation.observation_code.in_(codes))

    if sort_query:
        observations = observations.order_by(Observation.observation_time.desc())

    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return observations

    return observations.join(PatientRecord).filter(
        PatientRecord.sendingfacility.in_(units)
    )


def get_observation_codes(
    ukrdc3: Session,
    user: UKRDCUser,
    pid: Optional[str] = None,
) -> set[str]:
    """Get a list of available observation codes

    Args:
        ukrdc3 (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object
        pid (Optional[str], optional): PID of observation patientrecord. Defaults to None.

    Returns:
        list[str]: List of unique observation codes
    """
    observations = get_observations(ukrdc3, user, pid, sort_query=False)
    codes = observations.distinct(Observation.observation_code)
    return {item.observation_code for item in codes.all()}
