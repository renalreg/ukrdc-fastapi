from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord.observation import ObservationSchema


async def test_record_observations(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/observations"
    )
    assert response.status_code == 200

    items = response.json().get("items", [])
    assert len(items) > 0
    assert([ObservationSchema(**x) for x in items])

async def test_record_observations_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/observations"
    )
    assert response.status_code == 403

async def test_record_observation_codes(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/observation_codes"
    )
    assert response.status_code == 200
    assert set(response.json()) == {'bpdia', 'OBSERVATION_CODE', 'bpsys'}