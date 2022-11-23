from fastapi.exceptions import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord
from ukrdc_fastapi.utils import query_union
from ukrdc_fastapi.utils.records import INFORMATIONAL_FACILITIES, MEMBERSHIP_FACILITIES


def _assert_permission(ukrdc3: Session, patient_record: PatientRecord, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)

    # If the user has full admin permissions, return success
    if Permissions.UNIT_WILDCARD in units:
        return

    # Else, if the user has explicit facility-permission to access the record, return success
    if patient_record.sendingfacility in units:
        return

    # Otherwise, we have a more complicated situation like a multi-facility record.
    # We lean on our ability to determine permissions of groups of records
    if patient_record.ukrdcid:
        allowed_related_records = _get_patientrecords_from_ukrdcid(
            ukrdc3, patient_record.ukrdcid, user
        )

        # If the user has explicit permission to access another record with the same UKRDCID
        if patient_record.pid in (record.pid for record in allowed_related_records):
            return

    raise PermissionsError()


def _get_patientrecords_from_ukrdcid(
    ukrdc3: Session, ukrdcid: str, user: UKRDCUser
) -> Query:
    """
    Get a list of patient record the user has permission to acces, from a given UKRDCID.
    Multi-facility records like membership and informational records are included only if
    the user has facility-permissions to view at least one other record in the set.

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        ukrdcid (str): Patient UKRDC ID
        user (UKRDCUser): User object

    Returns:
        Query: Query producing a list of patient records
    """
    # Query all matching records, regardless of user permissions
    all_related_records = ukrdc3.query(PatientRecord).filter(
        PatientRecord.ukrdcid == ukrdcid
    )

    # If the user has full admin permissions, return all related records
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return all_related_records

    # Find which records the user has explicit facility-permission to access
    facility_allowed_records = all_related_records.filter(
        PatientRecord.sendingfacility.in_(units)
    )
    # If the user doesn't have permission to see any, return the currently-empty query
    if facility_allowed_records.count() < 1:
        return facility_allowed_records

    # Else, if the user has explicit facility-permission to see more than 1 matching record,
    # include multi-facility records like membership and informational records
    return all_related_records.filter(
        or_(
            PatientRecord.sendingfacility.in_(units),
            PatientRecord.sendingfacility.in_(MEMBERSHIP_FACILITIES),
            PatientRecord.sendingfacility.in_(INFORMATIONAL_FACILITIES),
        )
    )


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
    _assert_permission(ukrdc3, record, user)
    return record


def get_patientrecords_related_to_patientrecord(
    ukrdc3: Session, pid: str, user: UKRDCUser
) -> Query:
    """Get a query of PatientRecords with the same UKRDCID as a given PatientRecord

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        pid (str): PatientRecord PID
        user (UKRDCUser): User object

    Returns:
        Query: SQLAlchemy query
    """
    # TODO: Calling get_patientrecord is inefficient here as we're running
    #   two lots of permission queries, one for the individual record, and
    #   one during _get_patientrecords_from_ukrdcid.
    #   Ensures permission-safety, but there might be a way optimise if needed.
    record = get_patientrecord(ukrdc3, pid, user)

    if not record.ukrdcid:
        raise AttributeError(
            f"UKRDC ID for record {record.pid} is missing or NULL. This should never happen."
        )

    # Return all records with a matching UKRDC ID that the user has permission to access
    return _get_patientrecords_from_ukrdcid(ukrdc3, record.ukrdcid, user)


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
    # For the time being, it's possible for a patient to have multiple UKRDC IDs
    # Here, we get a list of all related UKRDC IDs from JTRACE
    related_ukrdc_records = get_masterrecords_related_to_masterrecord(
        jtrace, record_id, user
    ).filter(MasterRecord.nationalid_type == "UKRDC")

    # Strip whitespace. Needed until we fix the issue with fixed-length nationalid column
    related_ukrdcids = [record.nationalid.strip() for record in related_ukrdc_records]

    # Build queries for all records with matching UKRDC IDs that the user has permission to access
    record_queries = [
        _get_patientrecords_from_ukrdcid(ukrdc3, ukrdcid, user)
        for ukrdcid in related_ukrdcids
    ]

    # Create a query union from queries for each UKRDC ID
    return query_union(record_queries)
