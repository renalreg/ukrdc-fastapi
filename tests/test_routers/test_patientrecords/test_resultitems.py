from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord.laborder import ResultItemSchema


async def test_record_resultitems(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results"
    )
    assert response.status_code == 200

    items = response.json().get("items", [])
    assert len(items) > 0
    assert [ResultItemSchema(**x) for x in items]


async def test_resultitems_list_filtered_service_id(client_superuser):
    # Filter by NI
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results?service_id=SERVICE_ID_2"
    )
    assert response.status_code == 200


async def test_record_resultitems_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/results"
    )
    assert response.status_code == 403


async def test_resultitem_detail(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 200


async def test_resultitem_detail_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 403


async def test_resultitem_delete(client_superuser):
    response = await client_superuser.delete(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 204

    # Check the resultitem was deleted
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 404

    # Check the orphaned laborder was deleted
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER1"
    )
    assert response.status_code == 404


async def test_resultitem_delete_denied(client_authenticated):
    response = await client_authenticated.delete(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 403


async def test_record_resultitem_services(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/result_services"
    )
    assert response.status_code == 200
    item_ids = {item.get("id") for item in response.json()}
    assert item_ids == {"SERVICE_ID_1", "SERVICE_ID_2"}
