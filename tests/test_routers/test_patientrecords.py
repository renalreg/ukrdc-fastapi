from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema
from ukrdc_fastapi.config import configuration


def test_record(client):
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A"
    )
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST01:PV:00000000A"


def test_record_missing(client):
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:MISSING"
    )
    assert response.status_code == 404
