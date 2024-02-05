from typing import Any

from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem
from ukrdc_sqla.errorsdb import Latest, Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.base import OrmModel


class AdminCountsSchema(OrmModel):
    """Counts of various objects in the UKRDC"""

    open_workitems: int = Field(..., description="Number of open work items")
    distinct_patients: int = Field(
        ...,
        description="Number of distinct patients, calculated from the number of distinct UKRDC IDs in the database",
    )
    patients_receiving_errors: int = Field(
        ...,
        description="Number of patients whos most recently received file failed to be processed",
    )


def _int_or_zero(value: Any) -> int:
    """
    If the value is an int, return it, otherwise return 0.

    Really this is pointless as everywhere we use it we're
    counting rows, so it will always be an int, but it's
    here for completeness, and to make mypy happy.

    Args:
        value (Any): Value to check

    Returns:
        int: Value or 0
    """
    return value if isinstance(value, int) else 0


def _open_workitems_count(jtrace: Session) -> int:
    query = select(func.count()).select_from(WorkItem).where(WorkItem.status == 1)
    return _int_or_zero(jtrace.execute(query).scalar())


def _distinct_patients_count(ukrdc3: Session) -> int:
    query = select(func.count(PatientRecord.ukrdcid.distinct()))
    return _int_or_zero(ukrdc3.execute(query).scalar())


def _patients_receiving_errors_count(errorsdb: Session) -> int:
    query = (
        select(func.count())
        .select_from(Latest)
        .join(Message)
        .where(Message.msg_status == "ERROR")
    )
    return _int_or_zero(errorsdb.execute(query).scalar())


def get_admin_counts(
    ukrdc3: Session, jtrace: Session, errorsdb: Session
) -> AdminCountsSchema:
    """Retreive various counts across all facilities, available to admins

    Args:
        ukrdc3 (Session): UKRDC session
        jtrace (Session): JTRACE session
        errorsdb (Session): ErrorsDB session

    Returns:
        AdminCountsSchema: Counts of various items
    """
    return AdminCountsSchema(
        open_workitems=_open_workitems_count(jtrace),
        distinct_patients=_distinct_patients_count(ukrdc3),
        patients_receiving_errors=_patients_receiving_errors_count(errorsdb),
    )
