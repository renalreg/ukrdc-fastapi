from datetime import datetime

from ukrdc_fastapi.models.ukrdc import LabOrder


def test_laborders_list(client):
    response = client.get("/laborders")
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "LABORDER1",
                "entered_at_description": None,
                "entered_at": None,
                "specimen_collected_time": "2020-03-16T00:00:00",
            }
        ],
        "total": 1,
        "page": 0,
        "size": 50,
    }


def test_laborder(client):
    response = client.get("/laborders/LABORDER1")
    assert response.status_code == 200
    assert response.json() == {
        "id": "LABORDER1",
        "entered_at_description": None,
        "entered_at": None,
        "specimen_collected_time": "2020-03-16T00:00:00",
        "result_items": [
            {
                "id": "RESULTITEM1",
                "order_id": "LABORDER1",
                "service_id": "SERVICE_ID",
                "service_id_description": "SERVICE_ID_DESCRIPTION",
                "value": "VALUE",
                "value_units": "VALUE_UNITS",
            }
        ],
    }


def test_laborder_not_found(client):
    response = client.get("/laborders/MISSING")
    assert response.status_code == 404


def test_laborder_delete(client, ukrdc3_session):
    laborder = LabOrder(
        id="LABORDER_TEMP",
        pid="PYTEST01:PV:00000000A",
        external_id="EXTERNAL_ID_TEMP",
        order_category="ORDER_CATEGORY_TEMP",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    ukrdc3_session.add(laborder)
    ukrdc3_session.commit()

    # Make sure the laborder was created
    response = client.get("/laborders/LABORDER_TEMP")
    assert response.status_code == 200

    # Delete the lab order
    response = client.delete("/laborders/LABORDER_TEMP")
    assert response.status_code == 204

    # Make sure the lab order was deleted
    response = client.get("/laborders/LABORDER_TEMP")
    assert response.status_code == 404
