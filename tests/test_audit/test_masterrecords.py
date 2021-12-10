from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.schemas.empi import MasterRecordSchema


def test_masterrecord_detail(client, audit_session):
    response = client.get("/api/v1/masterrecords/1")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "MASTER_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None


def test_masterrecord_related(client, audit_session):
    # Check expected links

    response = client.get("/api/v1/masterrecords/1/related")
    assert response.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {4, 101, 104}

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 4

    primary_event = events[0]
    assert len(primary_event.children) == 3

    assert primary_event.resource == "MASTER_RECORD"
    assert primary_event.operation == "READ"
    assert primary_event.resource_id == "1"
    assert primary_event.parent_id == None

    for child_event in primary_event.children:
        assert child_event.resource == "MASTER_RECORD"
        assert child_event.operation == "READ"
        assert int(child_event.resource_id) in returned_ids
        assert child_event.parent_id == primary_event.id


def test_masterrecord_statistics(client, audit_session):
    response = client.get("/api/v1/masterrecords/1/statistics")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "MASTER_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "STATISTICS"
    assert child_event.operation == "READ"
    assert child_event.resource_id == None
    assert child_event.parent_id == event.id


# TODO: Link Records
# TODO: Messages
# TODO: Work Items
# TODO: Persons
# TODO: Patient Records
