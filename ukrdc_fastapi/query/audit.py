import datetime
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies.audit import Resource
from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent
from ukrdc_fastapi.query.masterrecords import (
    get_masterrecord,
    get_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecords_related_to_masterrecord,
)


def get_auditevents_related_to_masterrecord(
    audit: Session,
    ukrdc3: Session,
    jtrace: Session,
    record_id: int,
    user: UKRDCUser,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """
    Get all audit events related to a master record or any of its patient records.

    Args:
        audit (Session): AUDITDB SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        ukrdc3 (Session): UKRDC SQLAlchemy session
        record_id (str): MasterRecord ID
        user (UKRDCUser): User object

    Returns:
        Query: SQLAlchemy query
    """
    # Get the main record and check permissions
    record = get_masterrecord(jtrace, record_id, user)

    # Get all related master records
    master_records = get_masterrecords_related_to_masterrecord(
        jtrace, record.id, user, exclude_self=False
    )

    # Get all related patient records
    patient_records = get_patientrecords_related_to_masterrecord(
        ukrdc3, jtrace, record_id, user
    )

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

    if since:
        query = query.filter(AccessEvent.time >= since)

    if until:
        query = query.filter(AccessEvent.time <= until)

    return query.order_by(AuditEvent.id.desc())
