import datetime
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.audit import Resource
from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent
from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecords_related_to_masterrecord,
)


def get_auditevents_related_to_patientrecord(
    record: PatientRecord,
    audit: Session,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """Get all audit events related to a patient record

    Args:
        record (PatientRecord): Patient Record to audit
        audit (Session): Audit session
        since (Optional[datetime.datetime], optional): Since time. Defaults to None.
        until (Optional[datetime.datetime], optional): Until time. Defaults to None.

    Returns:
        Query: Audit query
    """

    query = (
        audit.query(AuditEvent)
        .join(AccessEvent)
        .filter(
            and_(
                AuditEvent.resource == Resource.PATIENT_RECORD.value,
                AuditEvent.resource_id == str(record.pid),
            )
        )
    )

    # Only show top-level events in the query. Child events are attached to parents
    query = query.filter(AuditEvent.parent_id.is_(None))

    if since:
        query = query.filter(AccessEvent.time >= since)

    if until:
        query = query.filter(AccessEvent.time <= until)

    return query


def get_auditevents_related_to_masterrecord(
    record: MasterRecord,
    audit: Session,
    ukrdc3: Session,
    jtrace: Session,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """Get all audit events related to a master record or any of its patient records.

    Args:
        record (MasterRecord): Master Record ORM object
        audit (Session): Audit session
        ukrdc3 (Session): UKRDC3 session
        jtrace (Session): JTRACE session
        since (Optional[datetime.datetime], optional): Since time. Defaults to None.
        until (Optional[datetime.datetime], optional): Until time. Defaults to None.

    Returns:
        Query: Audit query
    """
    # Get all related master records
    master_records = get_masterrecords_related_to_masterrecord(record, jtrace)

    # Get all related patient records
    patient_records = get_patientrecords_related_to_masterrecord(record, ukrdc3, jtrace)

    conditions = [
        and_(
            AuditEvent.resource == Resource.MASTER_RECORD.value,
            AuditEvent.resource_id.in_([str(mr.id) for mr in master_records]),
        ),
        and_(
            AuditEvent.resource == Resource.PATIENT_RECORD.value,
            AuditEvent.resource_id.in_([str(pr.pid) for pr in patient_records]),
        ),
    ]

    query = audit.query(AuditEvent).join(AccessEvent).filter(or_(*conditions))

    # Only show top-level events in the query. Child events are attached to parents
    query = query.filter(AuditEvent.parent_id.is_(None))

    if since:
        query = query.filter(AccessEvent.time >= since)

    if until:
        query = query.filter(AccessEvent.time <= until)

    return query
