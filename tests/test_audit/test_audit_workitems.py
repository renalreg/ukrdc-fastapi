from sqlalchemy import select
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.schemas.empi import WorkItemExtendedSchema, WorkItemSchema


def _verify_workitem_audit(workitem: WorkItemSchema, workitem_event: AuditEvent):
    assert workitem_event.resource == "WORKITEM"
    assert workitem_event.operation == "READ"
    assert workitem_event.resource_id == str(workitem.id)

    assert len(workitem_event.children) == 2

    master_record_event = [
        child for child in workitem_event.children if child.resource == "MASTER_RECORD"
    ][0]
    person_event = [
        child for child in workitem_event.children if child.resource == "PERSON"
    ][0]

    assert workitem.master_record
    assert workitem.person
    assert master_record_event.resource_id == str(workitem.master_record.id)
    assert person_event.resource_id == str(workitem.person.id)


def _verify_extended_workitem_audit(
    workitem: WorkItemExtendedSchema, workitem_event: AuditEvent
):
    assert workitem_event.resource == "WORKITEM"
    assert workitem_event.operation == "READ"
    assert workitem_event.resource_id == str(workitem.id)

    master_record_events = [
        child for child in workitem_event.children if child.resource == "MASTER_RECORD"
    ]
    person_events = [
        child for child in workitem_event.children if child.resource == "PERSON"
    ]

    expected_master_ids = set()
    expected_person_ids = set()

    assert workitem.destination.master_record
    assert workitem.incoming.person

    for master_record in workitem.incoming.master_records:
        expected_master_ids.add(str(master_record.id))
    for person in workitem.destination.persons:
        expected_person_ids.add(str(person.id))
    expected_master_ids.add(str(workitem.destination.master_record.id))
    expected_person_ids.add(str(workitem.incoming.person.id))

    assert len(expected_person_ids) == len(person_events)
    assert len(expected_master_ids) == len(master_record_events)

    for person_event in person_events:
        assert person_event.resource_id in expected_person_ids
    for master_record_event in master_record_events:
        assert master_record_event.resource_id in expected_master_ids


async def test_workitems_list(client_superuser, audit_session):
    response = await client_superuser.get(f"{configuration.base_url}/workitems")
    assert response.status_code == 200
    workitems = [WorkItemSchema(**wi) for wi in response.json().get("items")]

    events = audit_session.scalars(select(AuditEvent)).all()

    workitem_events = [event for event in events if event.resource == "WORKITEM"]
    assert len(workitem_events) == len(workitems)

    for workitem in workitems:
        _verify_workitem_audit(workitem, workitem_events.pop(0))


async def test_workitem_detail(client_superuser, audit_session):
    response = await client_superuser.get(f"{configuration.base_url}/workitems/1")
    assert response.status_code == 200
    wi = WorkItemExtendedSchema(**response.json())

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 6

    primary_event = events[0]
    assert len(primary_event.children) == 5

    _verify_extended_workitem_audit(wi, primary_event)


async def test_workitem_update(client_superuser, audit_session):
    response = await client_superuser.put(
        f"{configuration.base_url}/workitems/1",
        json={"status": 3, "comment": "UPDATE COMMENT"},
    )
    assert response.status_code == 200
    assert response.json().get("status") == "success"

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 1

    event = events[0]

    assert event.resource == "WORKITEM"
    assert event.operation == "UPDATE"
    assert event.resource_id == "1"


async def test_workitem_close(client_superuser, audit_session):
    response = await client_superuser.post(
        f"{configuration.base_url}/workitems/1/close", json={}
    )
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 1

    event = events[0]

    assert event.resource == "WORKITEM"
    assert event.operation == "UPDATE"
    assert event.resource_id == "1"


async def test_workitems_related(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems/1/related"
    )
    assert response.status_code == 200
    workitems = [WorkItemSchema(**wi) for wi in response.json()]
    returned_ids = {item.id for item in workitems}
    assert returned_ids == {2, 3, 4}

    events = audit_session.scalars(select(AuditEvent)).all()

    workitem_events = [event for event in events if event.resource == "WORKITEM"]
    assert len(workitem_events) == len(workitems)

    for workitem in workitems:
        _verify_workitem_audit(workitem, workitem_events.pop(0))


async def test_workitem_messages(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/workitems/1/messages"
    )
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "WORKITEM"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id is None

    child_event = event.children[0]
    assert child_event.resource == "MESSAGES"
    assert child_event.operation == "READ"
    assert child_event.parent_id == event.id
