import datetime
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.audit import AuditOperation, Resource
from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent


def get_auditevents_related_to_patientrecord(
    record: PatientRecord,
    audit: Session,
    resource: Optional[Resource] = None,
    operation: Optional[AuditOperation] = None,
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
            or_(
                and_(
                    AuditEvent.resource == Resource.PATIENT_RECORD.value,
                    AuditEvent.resource_id == str(record.pid),
                ),
                and_(
                    AuditEvent.resource == Resource.UKRDCID.value,
                    AuditEvent.resource_id == str(record.ukrdcid),
                ),
            )
        )
    )

    if resource:
        query = query.filter(AuditEvent.resource == resource.value)

    if operation:
        query = query.filter(AuditEvent.operation == operation.value)

    # Only show top-level events in the query. Child events are attached to parents
    query = query.filter(AuditEvent.parent_id.is_(None))

    if since:
        query = query.filter(AccessEvent.time >= since)

    if until:
        query = query.filter(AccessEvent.time <= until)

    return query
