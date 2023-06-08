from ukrdc_fastapi.config import configuration


async def test_record_dialysis_sessions(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/dialysissessions"
    )
    assert response.status_code == 200


async def test_record_dialysis_sessions_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/dialysissessions"
    )
    assert response.status_code == 403
