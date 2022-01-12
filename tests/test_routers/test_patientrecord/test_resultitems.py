from ukrdc_fastapi.schemas.laborder import ResultItemSchema
from ukrdc_fastapi.config import configuration


def test_record_resultitems(client):
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/results"
    )
    assert response.status_code == 200
    results = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert {result.id for result in results} == {
        "RESULTITEM1",
        "RESULTITEM2",
    }


def test_resultitems_list_filtered_serviceId(client):
    # Filter by NI
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/results?service_id=SERVICE_ID_2"
    )
    assert response.status_code == 200
    items = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert len(items) == 1
    assert items[0].service_id == "SERVICE_ID_2"


def test_resultitem_detail(client):
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1"
    )
    assert response.status_code == 200
    item = ResultItemSchema(**response.json())
    assert item.id == "RESULTITEM1"


def test_resultitem_delete(client):
    response = client.delete(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1/"
    )
    assert response.status_code == 204

    # Check the resultitem was deleted
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/results/RESULTITEM1/"
    )
    assert response.status_code == 404

    # Check the orphaned laborder was deleted
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/laborders/LABORDER1/"
    )
    assert response.status_code == 404
