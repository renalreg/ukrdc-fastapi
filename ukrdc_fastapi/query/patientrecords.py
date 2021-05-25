from fastapi.exceptions import HTTPException
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import Person
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.utils.links import find_related_ids


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.filter(PatientRecord.sendingfacility.in_(units))


def _assert_permission(patient_record: PatientRecord, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if patient_record.sendingfacility not in units:
        raise HTTPException(
            403,
            detail="You do not have permission to access this resource. Sending facility does not match.",
        )


def get_patientrecords(ukrdc3: Session, user: UKRDCUser) -> Query:
    records = ukrdc3.query(PatientRecord)
    return _apply_query_permissions(records, user)


def get_patientrecord(ukrdc3: Session, pid: str, user: UKRDCUser) -> PatientRecord:
    """Return a PatientRecord by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        pid (str): Patient ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        PatientRecord: PatientRecord
    """
    record = ukrdc3.query(PatientRecord).get(pid)
    if not record:
        raise HTTPException(404, detail="Record not found")
    _assert_permission(record, user)
    return record


def get_patientrecords_related_to_patientrecord(
    ukrdc3: Session, jtrace: Session, pid: str, user: UKRDCUser
) -> Query:
    record = get_patientrecord(ukrdc3, pid, user)

    # Get Person records directly related to the Patient Record
    record_persons = jtrace.query(Person).filter(Person.localid == record.pid)

    # Find all Person IDs indirectly related to the Person record
    _, related_person_ids = find_related_ids(
        jtrace, set(), {related_person.id for related_person in record_persons}
    )
    # Find all Person records in the list of related Person IDs
    related_persons = jtrace.query(Person).filter(Person.id.in_(related_person_ids))

    # Find all Patient IDs from the related Person records
    related_patient_ids = {person.localid for person in related_persons}

    # Find all Patient records in the list of related Patient IDs
    related_records = ukrdc3.query(PatientRecord).filter(
        PatientRecord.pid.in_(related_patient_ids)
    )

    return _apply_query_permissions(related_records, user)
