from datetime import datetime

from ukrdc_fastapi.models.ukrdc import (
    LabOrder,
    PatientNumber,
    PatientRecord,
    ResultItem,
)


def test_resultitems_list(client):
    response = client.get("/resultitems")
    assert response.status_code == 200
    print(response.json())
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
    ukrdc3_session.add(patient_record)
    ukrdc3_session.add(patient_number)
    ukrdc3_session.add(laborder)
    ukrdc3_session.add(resultitem)
    ukrdc3_session.commit()

    # Check we have multiple laborders when unfiltered
    response_unfiltered = client.get("/resultitems")
    assert len(response_unfiltered.json()["items"]) == 2

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
