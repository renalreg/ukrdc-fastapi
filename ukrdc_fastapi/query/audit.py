import datetime
from typing import Optional

from sqlalchemy import and_, or_, select
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
        resource (Optional[Resource]): Resource type value
        operation (Optional[Operation]): Operation type value
        since (Optional[datetime.datetime], optional): Since time. Defaults to None.
        until (Optional[datetime.datetime], optional): Until time. Defaults to None.

    Returns:
        Query: Audit query
    """

    # Recursively find audit events where the row or any parent of the row matches this patient
    topq = (
        audit.query(AuditEvent)
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
        .cte("cte", recursive=True)
    )

    bottomq = audit.query(AuditEvent)
    bottomq = bottomq.join(topq, AuditEvent.parent_id == topq.c.id)

    matched_ids_q = audit.query(topq.union(bottomq)).subquery()  # type: ignore

    # Create a query of all audit rows related to this patient

    q = (
        audit.query(AuditEvent)
        .join(AccessEvent)
        .filter(AuditEvent.id == matched_ids_q.c.id)
    )

    # Filter to rows matching date range
    if since:
        q = q.filter(AccessEvent.time >= since)

    if until:
        q = q.filter(AccessEvent.time <= until)

    # Filter to rows matching resource and operation

    if resource:
        q = q.filter(AuditEvent.resource == resource.value)

    if operation:
        q = q.filter(AuditEvent.operation == operation.value)

    # Remove children who's parent is already in the query

    subq = q.subquery()

    q_cleaned = (
        audit.query(AuditEvent)
        .join(AccessEvent)
        .filter(
            and_(
                AuditEvent.id
                == subq.c.id,  # Include rows that appeared in the main query...
                or_(  # ... but only include the subset of rows...
                    AuditEvent.parent_id.is_(
                        None
                    ),  # ...with no parent (top of the tree)...
                    AuditEvent.parent_id.notin_(
                        select([subq.c.id])
                    ),  # ...or who's parent isn't already included.
                ),
            )
        )
    )

    return q_cleaned
