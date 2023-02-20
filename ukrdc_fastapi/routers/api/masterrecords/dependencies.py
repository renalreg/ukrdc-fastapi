from typing import Optional

from fastapi.param_functions import Depends, Security
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.permissions.masterrecords import assert_masterrecord_permission

__all__ = ["_get_masterrecord"]


def _get_masterrecord(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
) -> MasterRecord:
    """Simple dependency to turn ID query param and User object into a MasterRecord object."""
    # Get the record
    record: Optional[MasterRecord] = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise ResourceNotFoundError("Master Record not found")

    # Check if the user has access to this record
    assert_masterrecord_permission(record, user)

    return record
