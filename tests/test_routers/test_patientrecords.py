from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema


def test_records(client):
    response = client.get("/api/v1/patientrecords")
    assert response.status_code == 200
    records = [PatientRecordSchema(**item) for item in response.json()["items"]]
    record_ids = {record.pid for record in records}
    assert record_ids == {"PYTEST01:PV:00000000A", "PYTEST02:PV:00000000A"}


def test_record(client):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A")
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST01:PV:00000000A"
