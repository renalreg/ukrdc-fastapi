from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.config import configuration


def test_access_event(client, audit_session):
    path = f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/"
    response = client.get(path)
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert event.resource == "PATIENT_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "PYTEST01:PV:00000000A"
    assert event.parent_id == None
    assert event.children == []

    access_event = events[0].access_event
    assert access_event.path == "http://testserver" + path
    assert access_event.sub == "TEST@UKRDC_FASTAPI"
    assert access_event.uid == "TEST_ID"
    assert access_event.cid == "PYTEST"
