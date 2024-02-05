from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord.medication import MedicationSchema


async def test_record_medications(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/medications"
    )
    assert response.status_code == 200

    # Check for validation errors
    assert len(response.json()) > 0
    assert [MedicationSchema(**x) for x in response.json()]


async def test_record_medications_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/medications"
    )
    assert response.status_code == 403
