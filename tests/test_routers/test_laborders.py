from datetime import datetime

from ukrdc_sqla.ukrdc import LabOrder, PatientNumber, PatientRecord, ResultItem

from ukrdc_fastapi.schemas.laborder import LabOrderSchema


def test_laborders_list(client):
    response = client.get("/api/laborders")
    assert response.status_code == 200
    assert {item.get("id") for item in response.json().get("items")} == {"LABORDER1"}


def test_laborder(client):
    response = client.get("/api/laborders/LABORDER1")
    assert response.status_code == 200
    order = LabOrderSchema(**response.json())
    assert order
    assert order.id == "LABORDER1"


def test_laborder_delete(client, ukrdc3_session):
    laborder = LabOrder(
        id="LABORDER_TEMP",
        pid="PYTEST01:PV:00000000A",
        external_id="EXTERNAL_ID_TEMP",
        order_category="ORDER_CATEGORY_TEMP",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    resultitem = ResultItem(
        id="RESULTITEM_TEMP",
        order_id="LABORDER_TEMP",
        service_id_std="SERVICE_ID_STD_TEMP",
        service_id="SERVICE_ID_TEMP",
        service_id_description="SERVICE_ID_DESCRIPTION_TEMP",
        value="VALUE_TEMP",
        value_units="VALUE_UNITS_TEMP",
        observation_time=datetime(2020, 3, 16),
    )
    ukrdc3_session.add(laborder)
    ukrdc3_session.add(resultitem)
    ukrdc3_session.commit()

    # Make sure the laborder was created
    assert ukrdc3_session.query(LabOrder).get("LABORDER_TEMP")
    assert ukrdc3_session.query(ResultItem).get("RESULTITEM_TEMP")
    response = client.get("/api/laborders/LABORDER_TEMP")
    assert response.status_code == 200

    # Delete the lab order
    response = client.delete("/api/laborders/LABORDER_TEMP/")
    assert response.status_code == 204

    # Make sure the lab order was deleted
    response = client.get("/api/laborders/LABORDER_TEMP/")
    assert response.status_code == 404
    assert not ukrdc3_session.query(LabOrder).get("LABORDER_TEMP")
    assert not ukrdc3_session.query(ResultItem).get("RESULTITEM_TEMP")
