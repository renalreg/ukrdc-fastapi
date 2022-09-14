from pydantic import Field
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem
from ukrdc_sqla.errorsdb import Latest, Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.base import OrmModel


class AdminCountsSchema(OrmModel):
    open_workitems: int = Field(..., description="Number of open work items")
    distinct_patients: int = Field(
        ...,
        description="Number of distinct patients, calculated from the number of distinct UKRDC IDs in the database",
    )
    patients_receiving_errors: int = Field(
        ...,
        description="Number of patients whos most recently received file failed to be processed",
    )


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
    open_workitems_count = jtrace.query(WorkItem).filter(WorkItem.status == 1).count()
    distinct_patients_count = ukrdc3.query(PatientRecord.ukrdcid).distinct().count()
    patients_receiving_errors_count = (
        errorsdb.query(Latest)
        .join(Message)
        .filter(Message.msg_status == "ERROR")
        .count()
    )

    return AdminCountsSchema(
        open_workitems=open_workitems_count,
        distinct_patients=distinct_patients_count,
        patients_receiving_errors=patients_receiving_errors_count,
    )
