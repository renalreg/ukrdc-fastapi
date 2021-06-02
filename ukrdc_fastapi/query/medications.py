from typing import Optional

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.ukrdc import Medication, PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


def get_medications(
    ukrdc3: Session,
    user: UKRDCUser,
    pid: Optional[str] = None,
) -> Query:
    """Get a list of medication records

    Args:
        ukrdc3 (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object
        pid (Optional[str], optional): PID of observation patientrecord. Defaults to None.

    Returns:
        Query: Medication query
    """
    medications = ukrdc3.query(Medication)

    if pid:
        medications = medications.filter(Medication.pid == pid)

    medications = medications.order_by(Medication.updated_on.desc())

    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return medications

    return medications.join(PatientRecord).filter(
        PatientRecord.sendingfacility.in_(units)
    )
