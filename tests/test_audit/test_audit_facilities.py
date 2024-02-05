from sqlalchemy import select
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.models.audit import AuditEvent


async def test_facility_messages(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/facilities/TSF01/patients_latest_errors"
    )
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "FACILITY"
    assert event.operation == "READ"
    assert event.resource_id == "TSF01"
    assert event.parent_id is None

    child_event = event.children[0]
    assert child_event.resource == "MESSAGES"
    assert child_event.operation == "READ"
    assert child_event.parent_id == event.id
