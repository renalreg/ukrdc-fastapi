from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.schemas.empi import MasterRecordSchema


def test_person_detail(client, audit_session):
    response = client.get("/api/v1/persons/1")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "PERSON"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None


def test_person_masterrecords(client, audit_session):
    response = client.get("/api/v1/persons/1/masterrecords")
    assert response.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {1, 101}

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    for event in events:
        assert event.resource == "MASTER_RECORD"
        assert event.operation == "READ"
        assert int(event.resource_id) in returned_ids
        assert event.parent_id == None
