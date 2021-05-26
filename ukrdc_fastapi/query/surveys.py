from typing import Optional

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.ukrdc import PatientRecord, Survey

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


def get_surveys(
    ukrdc3: Session,
    user: UKRDCUser,
    pid: Optional[str] = None,
) -> Query:
    """Get a list of patient surveys

    Args:
        ukrdc3 (Session): Database session
        user (UKRDCUser): Logged-in user object
        pid (Optional[str], optional): PID of survey PatientRecord. Defaults to None.

    Returns:
        Query: SQLAlchemy query of surveys
    """
    # Join with PatientRecord for unit permissions
    surveys = ukrdc3.query(Survey).join(PatientRecord.surveys)

    if pid:
        surveys = surveys.filter(Survey.pid == pid)

    surveys = surveys.order_by(Survey.surveytime.desc())

    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return surveys

    return surveys.filter(PatientRecord.sendingfacility.in_(units))
