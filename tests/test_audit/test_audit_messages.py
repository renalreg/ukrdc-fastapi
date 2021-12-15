import datetime

from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema


def test_messages_list(client, audit_session):
    response = client.get(f"/api/v1/messages/")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "MESSAGES"
    assert event.operation == "READ"
    assert event.resource_id == None
    assert event.parent_id == None


def test_message_detail(client, audit_session):
    response = client.get("/api/v1/messages/1")
    assert response.status_code == 200

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "MESSAGE"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None


def test_message_workitems(client, audit_session):
    response = client.get("/api/v1/messages/2/workitems")
    workitems = [WorkItemSchema(**item) for item in response.json()]

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 4

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "MESSAGE"
    assert event.operation == "READ"
    assert event.resource_id == "2"
    assert event.parent_id == None

    for i, workitem_event in enumerate(event.children):
        assert workitem_event.resource == "WORKITEM"
        assert workitem_event.operation == "READ"
        assert workitem_event.resource_id == str(workitems[i].id)
        assert workitem_event.parent_id == event.id

        assert len(workitem_event.children) == 2

        master_record_event = [
            child
            for child in workitem_event.children
            if child.resource == "MASTER_RECORD"
        ][0]
        person_event = [
            child for child in workitem_event.children if child.resource == "PERSON"
        ][0]

        assert master_record_event.resource_id == str(workitems[i].master_record.id)
        assert person_event.resource_id == str(workitems[i].person.id)


def test_message_masterrecords(client, audit_session):
    response = client.get("/api/v1/messages/1/masterrecords")
    assert response.status_code == 200
    returned_ids = {item.get("id") for item in response.json()}
    assert returned_ids == {1}

    events = audit_session.query(AuditEvent).all()
    assert len(events) == 2

    primary_event = events[0]
    assert len(primary_event.children) == 1

    assert primary_event.resource == "MESSAGE"
    assert primary_event.operation == "READ"
    assert primary_event.resource_id == "1"
    assert primary_event.parent_id == None

    for child_event in primary_event.children:
        assert child_event.resource == "MASTER_RECORD"
        assert child_event.operation == "READ"
        assert int(child_event.resource_id) in returned_ids
        assert child_event.parent_id == primary_event.id
