from sqlalchemy import select
from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.models.audit import AuditEvent
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema, WorkItemSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema


async def test_masterrecord_detail(client, audit_session):
    response = await client.get(f"{configuration.base_url}/masterrecords/1")
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 1

    event = events[0]
    assert len(event.children) == 0

    assert event.resource == "MASTER_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None


async def test_masterrecord_related(client_superuser, audit_session):
    # Check expected links

    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/related"
    )
    assert response.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {4, 101, 104}

    events = audit_session.scalars(select(AuditEvent)).all()
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


async def test_masterrecord_statistics(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/statistics"
    )
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
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


async def test_masterrecord_linkrecords(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/linkrecords"
    )
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 7

    event = events[0]
    assert len(event.children) == 6

    assert event.resource == "MASTER_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None

    for child_event in event.children:
        assert child_event.operation == "READ"

    person_events = [
        child_event
        for child_event in event.children
        if child_event.resource == "PERSON"
    ]
    assert len(person_events) == 2
    person_event_ids = {person_event.resource_id for person_event in person_events}
    assert person_event_ids == {"1", "4"}

    master_record_events = [
        child_event
        for child_event in event.children
        if child_event.resource == "MASTER_RECORD"
    ]
    assert len(master_record_events) == 4
    master_record_event_ids = {
        master_record_event.resource_id for master_record_event in master_record_events
    }
    assert master_record_event_ids == {"1", "101", "104", "4"}


async def test_masterrecord_messages(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/messages"
    )
    assert response.status_code == 200

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 2

    event = events[0]
    assert len(event.children) == 1

    assert event.resource == "MASTER_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "1"
    assert event.parent_id == None

    child_event = event.children[0]
    assert child_event.resource == "MESSAGES"
    assert child_event.operation == "READ"
    assert child_event.parent_id == event.id


async def test_masterrecord_workitems(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/workitems"
    )
    assert response.status_code == 200
    workitems = [WorkItemSchema(**item) for item in response.json()]

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 7

    event = events[0]
    assert len(event.children) == 2

    assert event.resource == "MASTER_RECORD"
    assert event.operation == "READ"
    assert event.resource_id == "1"
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


async def test_masterrecord_persons(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/persons"
    )
    assert response.status_code == 200
    persons = [PersonSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in persons}
    assert returned_ids == {1, 4}

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 3

    primary_event = events[0]
    assert len(primary_event.children) == 2

    assert primary_event.resource == "MASTER_RECORD"
    assert primary_event.operation == "READ"
    assert primary_event.resource_id == "1"
    assert primary_event.parent_id == None

    for child_event in primary_event.children:
        assert child_event.resource == "PERSON"
        assert child_event.operation == "READ"
        assert int(child_event.resource_id) in returned_ids
        assert child_event.parent_id == primary_event.id


async def test_masterrecord_patientrecords(client_superuser, audit_session):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/patientrecords"
    )
    assert response.status_code == 200
    records = [PatientRecordSummarySchema(**item) for item in response.json()]
    returned_pids = {item.pid for item in records}
    assert returned_pids == {"PYTEST01:PV:00000000A", "PYTEST04:PV:00000000A"}

    events = audit_session.scalars(select(AuditEvent)).all()
    assert len(events) == 3

    primary_event = events[0]
    assert len(primary_event.children) == 2

    assert primary_event.resource == "MASTER_RECORD"
    assert primary_event.operation == "READ"
    assert primary_event.resource_id == "1"
    assert primary_event.parent_id == None

    for child_event in primary_event.children:
        assert child_event.resource == "PATIENT_RECORD"
        assert child_event.operation == "READ"
        assert child_event.resource_id in returned_pids
        assert child_event.parent_id == primary_event.id
