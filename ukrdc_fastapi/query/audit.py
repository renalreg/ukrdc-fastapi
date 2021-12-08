from sqlalchemy import and_, or_
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies.audit import Resource
from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.query.masterrecords import (
    get_masterrecord,
    get_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecords_related_to_masterrecord,
)


def get_auditevents_related_to_masterrecord(
    audit: Session, jtrace: Session, ukrdc3: Session, record_id: int, user: UKRDCUser
):
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

    return audit.query(AuditEvent).filter(or_(*conditions))
