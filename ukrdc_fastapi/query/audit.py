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
        resource (Optional[Resource]): Resource type value
        operation (Optional[Operation]): Operation type value
        since (Optional[datetime.datetime], optional): Since time. Defaults to None.
        until (Optional[datetime.datetime], optional): Until time. Defaults to None.

    Returns:
        Query: Audit query
    """

    # Recursive query to fetch all rows where resource and operation match, unless unspecified
    query = audit.query(AuditEvent).filter(
        or_(
            AuditEvent.resource == (resource.value if resource else None),
            resource is None,
        ),
        or_(
            AuditEvent.operation == (operation.value if operation else None),
            operation is None,
        ),
    )
    recursive_query = query.cte(recursive=True)

    # Join the recursive query with the original table, but only keep the top-level parent rows.
    # This way, we return just the parents of any child rows that match the resource and operation values specified.
    # This happens recursively, e.g. if a child of a child of a parent matches the condition, that parent is returned.
    top_level_parents_query = (
        audit.query(AuditEvent)
        .outerjoin(recursive_query, AuditEvent.id == recursive_query.c.parent_id)
        .filter(AuditEvent.parent_id.is_(None))
    )

    # Filter to top-level parent rows matching PID or UKRDCID, and turn into a subquery
    matching_top_level_parents_subquery = top_level_parents_query.filter(
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
    ).subquery()

    # Find all audit events where the event ID appears in the subquery above.
    # If we don't create this fresh, simple query then filtering by AccessEvent attributes
    # won't reliably work, so all "simple" filters should happen here.
    query_to_return = (
        audit.query(AuditEvent)
        .join(AccessEvent)
        .filter(AuditEvent.id == matching_top_level_parents_subquery.c.id)
    )

    # Filter to top-level parent rows matching date range
    if since:
        query_to_return = query_to_return.filter(AccessEvent.time >= since)

    if until:
        query_to_return = query_to_return.filter(AccessEvent.time <= until)

    return query_to_return
