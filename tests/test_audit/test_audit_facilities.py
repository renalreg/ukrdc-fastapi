from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.models.audit import AuditEvent


async def test_facility_messages(client, audit_session):
    response = await client.get(
        f"{configuration.base_url}/v1/facilities/TEST_SENDING_FACILITY_1/patients_latest_errors"
    )
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "FACILITY"
    assert event.operation == "READ"
    assert event.resource_id == "TEST_SENDING_FACILITY_1"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "MESSAGES"
    assert child_event.operation == "READ"
    assert child_event.parent_id == event.id
