from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem
from ukrdc_sqla.errorsdb import Latest, Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.base import OrmModel


class AdminCountsSchema(OrmModel):
    open_workitems: int
    distinct_patients: int
    patients_receiving_errors: int


def get_admin_counts(ukrdc3: Session, jtrace: Session, errorsdb: Session):
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
