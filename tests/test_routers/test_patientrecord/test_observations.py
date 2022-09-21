from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.observation import ObservationSchema


async def test_record_observations(client):
    response = await client.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/observations"
    )
    assert response.status_code == 200
    observations = [ObservationSchema(**item) for item in response.json()["items"]]
    assert len(observations) == 3
