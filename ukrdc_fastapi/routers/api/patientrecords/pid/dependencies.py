from fastapi.param_functions import Depends, Security
from sqlalchemy.orm.session import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.permissions.patientrecords import assert_patientrecord_permission

__all__ = ["_get_patientrecord"]


def _get_patientrecord(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> PatientRecord:
    """Simple dependency to turn pid query param and User object into a PatientRecord object."""
    record = ukrdc3.query(PatientRecord).get(pid)

    if not record:
        raise ResourceNotFoundError("Record not found")

    assert_patientrecord_permission(record, ukrdc3, user)
    return record
