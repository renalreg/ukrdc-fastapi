from fastapi.exceptions import HTTPException
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord, Person
from ukrdc_sqla.ukrdc import PatientRecord
from ukrdc_sqla.utils.links import find_related_ids

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord


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
        raise PermissionsError()


def get_patientrecords(ukrdc3: Session, user: UKRDCUser) -> Query:
    """Get a list of PatientRecords

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        user (UKRDCUser): User object

    Returns:
        Query: SQLAlchemy query
    """
    records = ukrdc3.query(PatientRecord)
    return _apply_query_permissions(records, user)


def get_patientrecord(ukrdc3: Session, pid: str, user: UKRDCUser) -> PatientRecord:
    """Return a PatientRecord by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        pid (str): Patient ID
        user (UKRDCUser): User object

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
    """Get a query of PatientRecords related via the LinkRecord network to a given PatientRecord

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        pid (str): PatientRecord PID
        user (UKRDCUser): User object

    Returns:
        Query: SQLAlchemy query
    """
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


def get_patientrecords_related_to_masterrecord(
    ukrdc3: Session, jtrace: Session, record_id: int, user: UKRDCUser
) -> Query:
    """
    Get a list of patient records related to a Master Record.

    First finds all UKRDC Master Records linked to the given record ID via
    the LinkRecord tree. Then returns a list of all Patient Records with a
    UKRDC ID in that list.

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (str): MasterRecord ID
        user (UKRDCUser): User object

    Returns:
        Query: SQLAlchemy query
    """
    related_ukrdc_records = get_masterrecords_related_to_masterrecord(
        jtrace, record_id, user, exclude_self=False
    ).filter(MasterRecord.nationalid_type == "UKRDC")

    # Strip whitespace. Needed until we fix the issue with fixed-length nationalid column
    related_ukrdcids = [record.nationalid.strip() for record in related_ukrdc_records]

    related_records = get_patientrecords(ukrdc3, user).filter(
        PatientRecord.ukrdcid.in_(related_ukrdcids)
    )

    return _apply_query_permissions(related_records, user)
