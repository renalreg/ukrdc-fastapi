from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema


async def test_record(client):
    response = await client.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A"
    )
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST01:PV:00000000A"


async def test_record_missing(client):
    response = await client.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:MISSING"
    )
    assert response.status_code == 404
