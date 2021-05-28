from datetime import datetime

from ukrdc_sqla.ukrdc import LabOrder, PatientNumber, PatientRecord, ResultItem

from ukrdc_fastapi.schemas.laborder import LabOrderShortSchema, ResultItemSchema


def _commit_extra_resultitem(session):
    patient_record = PatientRecord(
        pid="PYTEST01:LABORDERS:00000000L",
        sendingfacility="PATIENT_RECORD_SENDING_FACILITY_1",
        sendingextract="PV",
        localpatientid="00000000L",
        ukrdcid="000000001",
        repository_update_date=datetime(2020, 3, 16),
        repository_creation_date=datetime(2020, 3, 16),
    )
    patient_number = PatientNumber(
        id=2,
        pid="PYTEST01:LABORDERS:00000000L",
        patientid="111111111",
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
    response_unfiltered = client.get("/api/resultitems")
    assert len(response_unfiltered.json()["items"]) == 1

    # Add an extra test item
    _commit_extra_resultitem(session)

    # Check we have multiple laborders when unfiltered
    response_unfiltered = client.get("/api/resultitems")
    assert len(response_unfiltered.json()["items"]) == 2


def test_resultitems_list(client):
    response = client.get("/api/resultitems")
    assert response.status_code == 200
    items = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert len(items) == 1
    assert items[0].id == "RESULTITEM1"


def test_resultitems_list_filtered_serviceId(ukrdc3_session, client):
    # Add an extra test item
    _commit_extra_resultitem_and_check(ukrdc3_session, client)

    # Filter by NI
    response = client.get("/api/resultitems?service_id=SERVICE_ID_TEST2_1")
    assert response.status_code == 200
    items = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert len(items) == 1
    assert items[0].id == "RESULTITEM_TEST2_1"


def test_resultitem_detail(client):
    response = client.get("/api/resultitems/RESULTITEM1")
    assert response.status_code == 200
    item = ResultItemSchema(**response.json())
    assert item.id == "RESULTITEM1"


def test_resultitem_delete(client):
    response = client.delete("/api/resultitems/RESULTITEM1/")
    assert response.status_code == 204

    # Check the resultitem was deleted
    response = client.get("/api/resultitems/")
    assert response.status_code == 200
    assert response.json()["items"] == []

    # Check the orphaned laborder was deleted
    response = client.get("/api/laborders/")
    assert response.status_code == 200
    assert response.json()["items"] == []
