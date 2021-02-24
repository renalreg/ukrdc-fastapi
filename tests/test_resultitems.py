from datetime import datetime

from ukrdc_fastapi.models.ukrdc import (
    LabOrder,
    PatientNumber,
    PatientRecord,
    ResultItem,
)


def _commit_extra_resultitem(session):
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
        id="LABORDER_TEST2_1",
        pid="PYTEST01:LABORDERS:00000000L",
        external_id="EXTERNAL_ID_TEST2_1",
        order_category="ORDER_CATEGORY_TEST2_1",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    resultitem = ResultItem(
        id="RESULTITEM_TEST2_1",
        order_id="LABORDER_TEST2_1",
        service_id_std="SERVICE_ID_STD_TEST2_1",
        service_id="SERVICE_ID_TEST2_1",
        service_id_description="SERVICE_ID_DESCRIPTION_TEST2_1",
        value="VALUE_TEST2_1",
        value_units="VALUE_UNITS_TEST2_1",
        observation_time=datetime(2020, 3, 16),
    )
    session.add(patient_record)
    session.add(patient_number)
    session.add(laborder)
    session.add(resultitem)
    session.commit()


def _commit_extra_resultitem_and_check(session, client):
    # Check we have no unexpected items
    response_unfiltered = client.get("/resultitems")
    assert len(response_unfiltered.json()["items"]) == 1

    # Add an extra test item
    _commit_extra_resultitem(session)

    # Check we have multiple laborders when unfiltered
    response_unfiltered = client.get("/resultitems")
    assert len(response_unfiltered.json()["items"]) == 2


def test_resultitems_list(client):
    response = client.get("/resultitems")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": "RESULTITEM1",
            "order_id": "LABORDER1",
            "service_id": "SERVICE_ID",
            "service_id_description": "SERVICE_ID_DESCRIPTION",
            "value": "VALUE",
            "value_units": "VALUE_UNITS",
        }
    ]


def test_resultitems_list_filtered_ni(ukrdc3_session, client):
    # Add an extra test item
    _commit_extra_resultitem_and_check(ukrdc3_session, client)

    # Filter by NI
    response = client.get("/resultitems?ni=111111111")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": "RESULTITEM_TEST2_1",
            "order_id": "LABORDER_TEST2_1",
            "service_id": "SERVICE_ID_TEST2_1",
            "service_id_description": "SERVICE_ID_DESCRIPTION_TEST2_1",
            "value": "VALUE_TEST2_1",
            "value_units": "VALUE_UNITS_TEST2_1",
        },
    ]


def test_resultitems_list_filtered_service_id(ukrdc3_session, client):
    # Add an extra test item
    _commit_extra_resultitem_and_check(ukrdc3_session, client)

    # Filter by NI
    response = client.get("/resultitems?service_id=SERVICE_ID_TEST2_1")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": "RESULTITEM_TEST2_1",
            "order_id": "LABORDER_TEST2_1",
            "service_id": "SERVICE_ID_TEST2_1",
            "service_id_description": "SERVICE_ID_DESCRIPTION_TEST2_1",
            "value": "VALUE_TEST2_1",
            "value_units": "VALUE_UNITS_TEST2_1",
        },
    ]


def test_resultitems_list_filtered_service_id_delete(ukrdc3_session, client):
    # Add an extra test item
    _commit_extra_resultitem_and_check(ukrdc3_session, client)

    # Filter by NI
    response = client.delete("/resultitems/", json={"service_id": "SERVICE_ID_TEST2_1"})
    assert response.status_code == 204

    # Check the resultitem was deleted
    response = client.get("/resultitems")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": "RESULTITEM1",
            "order_id": "LABORDER1",
            "service_id": "SERVICE_ID",
            "service_id_description": "SERVICE_ID_DESCRIPTION",
            "value": "VALUE",
            "value_units": "VALUE_UNITS",
        }
    ]
    # Check the orphaned laborder was deleted
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


def test_resultitem_detail(client):
    response = client.get("/resultitems/RESULTITEM1")
    assert response.status_code == 200
    assert response.json() == {
        "id": "RESULTITEM1",
        "order_id": "LABORDER1",
        "service_id": "SERVICE_ID",
        "service_id_description": "SERVICE_ID_DESCRIPTION",
        "value": "VALUE",
        "value_units": "VALUE_UNITS",
    }


def test_resultitem_delete(client):
    response = client.delete("/resultitems/RESULTITEM1")
    assert response.status_code == 204

    # Check the resultitem was deleted
    response = client.get("/resultitems")
    assert response.status_code == 200
    assert response.json()["items"] == []

    # Check the orphaned laborder was deleted
    response = client.get("/laborders")
    assert response.status_code == 200
    assert response.json()["items"] == []
