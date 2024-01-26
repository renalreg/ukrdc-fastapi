import datetime
from typing import Optional

from sqlalchemy import and_, not_, or_, select
from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.audit import AuditOperation, Resource
from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent


def select_auditevents_related_to_patientrecord(
    record: PatientRecord,
    resource: Optional[Resource] = None,
    operation: Optional[AuditOperation] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Select:
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
        select(AuditEvent)
        .where(
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

    bottomq = select(AuditEvent).join(topq, AuditEvent.parent_id == topq.c.id)

    matched_ids_q = select(topq.union(bottomq)).subquery()

    # Create a query of all audit rows related to this patient
    q = select(AuditEvent).join(AccessEvent).where(AuditEvent.id == matched_ids_q.c.id)

    # Filter to rows matching date range
    if since:
        q = q.where(AccessEvent.time >= since)

    if until:
        q = q.where(AccessEvent.time <= until)

    # Filter to rows matching resource and operation
    if resource:
        q = q.where(AuditEvent.resource == resource.value)

    if operation:
        q = q.where(AuditEvent.operation == operation.value)

    # Remove children whose parent is already in the query
    subq = q.subquery()

    q_cleaned = (
        select(AuditEvent)
        .join(AccessEvent)
        .where(
            and_(
                AuditEvent.id
                == subq.c.id,  # Include rows that appeared in the main query...
                or_(  # ... but only include the subset of rows...
                    AuditEvent.parent_id.is_(
                        None
                    ),  # ...with no parent (top of the tree)...
                    not_(
                        AuditEvent.parent_id.in_(select(subq.c.id))
                    ),  # ...or whose parent isn't already included.
                ),
            )
        )
    )

    return q_cleaned
