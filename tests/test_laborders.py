from datetime import datetime

from ukrdc_fastapi.models.ukrdc import (
    LabOrder,
    PatientNumber,
    PatientRecord,
    ResultItem,
)


def test_laborders_list(client):
    response = client.get("/laborders")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": "LABORDER1",
            "href": "/laborders/LABORDER1",
            "entered_at_description": None,
            "entered_at": None,
            "specimen_collected_time": "2020-03-16T00:00:00",
        }
    ]


def test_laborders_list_filtered_ni(ukrdc3_session, client):
    patient_record = PatientRecord(
        pid="PYTEST01:LABORDERS:00000000L",
        sendingfacility="PATIENT_RECORD_SENDING_FACILITY_1",
        sendingextract="PV",
        localpatientid="00000000L",
        ukrdcid="000000001",
        lastupdated=datetime(2020, 3, 16),
        repository_creation_date=datetime(2020, 3, 16),
    )
    patient_number = PatientNumber(
        id=2,
        pid="PYTEST01:LABORDERS:00000000L",
        number="111111111",
        organization="NHS",
        numbertype="NI",
    )
    laborder = LabOrder(
        id="LABORDER_TEST1_1",
        pid="PYTEST01:LABORDERS:00000000L",
        external_id="EXTERNAL_ID_TEST1_1",
        order_category="ORDER_CATEGORY_TEST1_1",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    ukrdc3_session.add(patient_record)
    ukrdc3_session.add(patient_number)
    ukrdc3_session.add(laborder)
    ukrdc3_session.commit()

    # Check we have multiple laborders when unfiltered
    response_unfiltered = client.get("/laborders")
    assert len(response_unfiltered.json()["items"]) == 2

    # Filter by NI
    response = client.get("/laborders?ni=111111111")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": "LABORDER_TEST1_1",
            "href": "/laborders/LABORDER_TEST1_1",
            "entered_at_description": None,
            "entered_at": None,
            "specimen_collected_time": "2020-03-16T00:00:00",
        }
    ]


def test_laborder(client):
    response = client.get("/laborders/LABORDER1")
    assert response.status_code == 200
    assert response.json() == {
        "id": "LABORDER1",
        "href": "/laborders/LABORDER1",
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
    response = client.get("/laborders/LABORDER_TEMP")
    assert response.status_code == 200

    # Delete the lab order
    response = client.delete("/laborders/LABORDER_TEMP")
    assert response.status_code == 204

    # Make sure the lab order was deleted
    response = client.get("/laborders/LABORDER_TEMP")
    assert response.status_code == 404
    assert not ukrdc3_session.query(LabOrder).get("LABORDER_TEMP")
    assert not ukrdc3_session.query(ResultItem).get("RESULTITEM_TEMP")
