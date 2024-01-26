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


def _open_workitems_count(jtrace: Session) -> int:
    query = select(func.count()).select_from(WorkItem).filter(WorkItem.status == 1)
    result = jtrace.execute(query)
    return result.scalar()


def _distinct_patients_count(ukrdc3: Session) -> int:
    query = select(func.count(PatientRecord.ukrdcid.distinct()))
    result = ukrdc3.execute(query)
    return result.scalar()


def _patients_receiving_errors_count(errorsdb: Session) -> int:
    query = (
        select(func.count())
        .select_from(Latest)
        .join(Message)
        .filter(Message.msg_status == "ERROR")
    )
    result = errorsdb.execute(query)
    return result.scalar()


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
