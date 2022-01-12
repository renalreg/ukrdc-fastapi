from ukrdc_fastapi.routers.api.v1.masterrecords.record_id import (
    MasterRecordStatisticsSchema,
)
from ukrdc_fastapi.schemas.empi import (
    LinkRecordSchema,
    MasterRecordSchema,
    PersonSchema,
    WorkItemSchema,
)
from ukrdc_fastapi.schemas.message import MessageSchema, MinimalMessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema
from ukrdc_fastapi.config import configuration


def test_masterrecord_detail(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1")
    assert response.status_code == 200
    mr = MasterRecordSchema(**response.json())
    assert mr.id == 1


def test_masterrecord_related(client, jtrace_session):
    # Check expected links

    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/related")
    assert response.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {4, 101, 104}

    # Test reciprocal link

    response_reciprocal = client.get(
        f"{configuration.base_url}/v1/masterrecords/4/related"
    )
    assert response_reciprocal.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response_reciprocal.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {1, 101, 104}


def test_masterrecord_latest_message(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/latest_message")
    assert response.status_code == 200

    message = MinimalMessageSchema(**response.json())
    assert message.id == 1


def test_masterrecord_statistics(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/statistics")
    assert response.status_code == 200

    stats = MasterRecordStatisticsSchema(**response.json())
    assert stats.workitems == 2
    assert stats.errors == 1
    assert stats.ukrdcids == 2


def test_masterrecord_linkrecords(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/linkrecords")
    assert response.status_code == 200

    records = [LinkRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in records}
    assert returned_ids == {1, 4, 101, 104, 401}


def test_masterrecord_workitems(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/workitems")
    assert response.status_code == 200

    witems = [WorkItemSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in witems}
    assert returned_ids == {1, 2}


def test_masterrecord_errors(client):
    response = client.get(
        f"{configuration.base_url}/v1/masterrecords/1/messages/?status=ERROR"
    )
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in errors}
    assert returned_ids == {1}


def test_masterrecord_messages(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/messages")
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in errors}
    assert returned_ids == {1, 3}


def test_masterrecord_persons(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/persons")
    assert response.status_code == 200

    persons = [PersonSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in persons}
    assert returned_ids == {1, 4}


def test_masterrecord_patientrecords(client):
    response = client.get(f"{configuration.base_url}/v1/masterrecords/1/patientrecords")
    assert response.status_code == 200

    records = [PatientRecordSummarySchema(**item) for item in response.json()]
    pids = {record.pid for record in records}
    assert pids == {"PYTEST01:PV:00000000A", "PYTEST04:PV:00000000A"}
