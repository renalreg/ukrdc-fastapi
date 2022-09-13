from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.routers.api.masterrecords.record_id import (
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
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema


async def test_masterrecord_detail(client):
    response = await client.get(f"{configuration.base_url}/masterrecords/1")
    assert response.status_code == 200
    mr = MasterRecordSchema(**response.json())
    assert mr.id == 1


async def test_masterrecord_related(client):
    # Check expected links

    response = await client.get(f"{configuration.base_url}/masterrecords/1/related")
    assert response.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {4, 101, 104}

    # Test reciprocal link

    response_reciprocal = await client.get(
        f"{configuration.base_url}/masterrecords/4/related"
    )
    assert response_reciprocal.status_code == 200
    mrecs = [MasterRecordSchema(**item) for item in response_reciprocal.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {1, 101, 104}


async def test_masterrecord_latest_message(client):
    response = await client.get(
        f"{configuration.base_url}/masterrecords/1/latest_message"
    )
    assert response.status_code == 200

    message = MinimalMessageSchema(**response.json())
    assert message.id == 2


async def test_masterrecord_statistics(client):
    response = await client.get(f"{configuration.base_url}/masterrecords/1/statistics")
    assert response.status_code == 200

    stats = MasterRecordStatisticsSchema(**response.json())
    assert stats.workitems == 2
    assert stats.errors == 1
    assert stats.ukrdcids == 2


async def test_masterrecord_linkrecords(client):
    response = await client.get(f"{configuration.base_url}/masterrecords/1/linkrecords")
    assert response.status_code == 200

    records = [LinkRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in records}
    assert returned_ids == {1, 4, 101, 104, 401}


async def test_masterrecord_workitems(client):
    response = await client.get(f"{configuration.base_url}/masterrecords/1/workitems")
    assert response.status_code == 200

    witems = [WorkItemSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in witems}
    assert returned_ids == {1, 2}


async def test_masterrecord_errors(client):
    response = await client.get(
        f"{configuration.base_url}/masterrecords/1/messages?status=ERROR"
    )
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in errors}
    assert returned_ids == {2}


async def test_masterrecord_messages(client):
    response = await client.get(f"{configuration.base_url}/masterrecords/1/messages")
    assert response.status_code == 200

    errors = [MessageSchema(**item) for item in response.json()["items"]]
    returned_ids = {item.id for item in errors}
    assert returned_ids == {1, 2}


async def test_masterrecord_persons(client):
    response = await client.get(f"{configuration.base_url}/masterrecords/1/persons")
    assert response.status_code == 200

    persons = [PersonSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in persons}
    assert returned_ids == {1, 4}


async def test_masterrecord_patientrecords(client):
    response = await client.get(
        f"{configuration.base_url}/masterrecords/1/patientrecords"
    )
    assert response.status_code == 200

    records = [PatientRecordSummarySchema(**item) for item in response.json()]
    pids = {record.pid for record in records}
    assert pids == {"PYTEST01:PV:00000000A", "PYTEST04:PV:00000000A"}


async def test_master_record_memberships_create_pkb(client):
    response = await client.post(
        f"{configuration.base_url}/masterrecords/2/memberships/create/pkb"
    )
    assert response.status_code == 200
    resp = MirthMessageResponseSchema(**response.json())
    assert resp.status == "success"
    assert resp.message == "<result><ukrdcid>999999911</ukrdcid></result>"


async def test_master_record_memberships_create_pkb_non_ukrdc(client):
    response = await client.post(
        f"{configuration.base_url}/masterrecords/102/memberships/create/pkb"
    )
    assert response.status_code == 200
    resp = MirthMessageResponseSchema(**response.json())
    assert resp.status == "success"
    assert resp.message == "<result><ukrdcid>999999911</ukrdcid></result>"
