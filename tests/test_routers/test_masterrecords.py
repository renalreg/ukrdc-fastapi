from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema


async def test_masterrecord_detail(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1"
    )
    assert response.status_code == 200


async def test_masterrecord_detail_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2"
    )
    assert response.status_code == 403


async def test_masterrecord_related(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/related"
    )
    assert response.status_code == 200


async def test_masterrecord_related_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/related"
    )
    assert response.status_code == 403


async def test_masterrecord_latest_message(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/latest_message"
    )
    assert response.status_code == 200


async def test_masterrecord_latest_message_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/latest_message"
    )
    assert response.status_code == 403


async def test_masterrecord_statistics(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/statistics"
    )
    assert response.status_code == 200


async def test_masterrecord_statistics_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/statistics"
    )
    assert response.status_code == 403


async def test_masterrecord_linkrecords(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/linkrecords"
    )
    assert response.status_code == 200


async def test_masterrecord_linkrecords_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/linkrecords"
    )
    assert response.status_code == 403


async def test_masterrecord_workitems(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/workitems"
    )
    assert response.status_code == 200

    witems = [WorkItemSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in witems}
    assert returned_ids == {1}


async def test_masterrecord_workitems_superuser(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/masterrecords/1/workitems"
    )
    assert response.status_code == 200

    witems = [WorkItemSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in witems}
    assert returned_ids == {1, 2}


async def test_masterrecord_workitems_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/workitems"
    )
    assert response.status_code == 403


async def test_masterrecord_messages(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/messages"
    )
    assert response.status_code == 200


async def test_masterrecord_messages_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/messages"
    )
    assert response.status_code == 403


async def test_masterrecord_persons(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/persons"
    )
    assert response.status_code == 200


async def test_masterrecord_persons_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/persons"
    )
    assert response.status_code == 403


async def test_masterrecord_patientrecords(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/1/patientrecords"
    )
    assert response.status_code == 200

    records = [PatientRecordSummarySchema(**item) for item in response.json()]
    pids = {record.pid for record in records}
    assert pids == {"PYTEST01:PV:00000000A", "PYTEST04:PV:00000000A"}


async def test_masterrecord_patientrecords_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/masterrecords/2/patientrecords"
    )
    assert response.status_code == 403
