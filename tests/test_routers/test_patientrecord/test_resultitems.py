from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.laborder import ResultItemSchema


async def test_record_resultitems(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results"
    )
    assert response.status_code == 200
    results = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert {result.id for result in results} == {
        "RESULTITEM1",
        "RESULTITEM2",
    }


async def test_resultitems_list_filtered_serviceId(client_superuser):
    # Filter by NI
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results?service_id=SERVICE_ID_2"
    )
    assert response.status_code == 200
    items = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert len(items) == 1
    assert items[0].service_id == "SERVICE_ID_2"


async def test_resultitem_detail(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 200
    item = ResultItemSchema(**response.json())
    assert item.id == "RESULTITEM1"


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
