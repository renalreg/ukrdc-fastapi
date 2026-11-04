from ukrdc_sqla.ukrdc import Observation, PatientRecord

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord.observation import (
    ObservationSchema,
    ObservationTrendPointSchema,
)


async def test_record_observations(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/observations"
    )
    assert response.status_code == 200

    items = response.json().get("items", [])
    assert len(items) > 0
    assert [ObservationSchema(**x) for x in items]


async def test_record_observations_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03PV/observations"
    )
    assert response.status_code == 403


async def test_record_observation_codes(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/observation_codes"
    )
    assert response.status_code == 200
    assert set(response.json()) == {"bpdia", "OBSERVATION_CODE", "bpsys"}


async def test_ui_261(client_superuser, ukrdc3_session):
    # Update to the pydantic schema to allow null values

    obs = (
        ukrdc3_session.query(PatientRecord)
        .join(Observation)
        .where(PatientRecord.pid == "PYTEST01PV")
        .first()
        .observations[0]
    )
    obs.observationvalue = None
    ukrdc3_session.commit()

    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/observations"
    )
    assert response.status_code == 200

    items = response.json().get("items", [])
    assert len(items) > 0
    assert [ObservationSchema(**x) for x in items]


async def test_observations_trend(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/observations/trend?code=bpsys"
    )
    assert response.status_code == 200

    items = response.json()
    assert len(items) > 0
    assert [ObservationTrendPointSchema(**x) for x in items]


async def test_observations_trend_oldest_first(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01PV/observations/trend?code=bpsys"
    )
    assert response.status_code == 200

    times = [item["observationTime"] for item in response.json()]
    assert len(times) > 1
    assert times == sorted(times)


async def test_observations_trend_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03PV/observations/trend?code=bpsys"
    )
    assert response.status_code == 403


async def test_observations_trend_matches_list(client_superuser):
    base = f"{configuration.base_url}/patientrecords/PYTEST01PV/observations"

    list_response = await client_superuser.get(f"{base}?code=bpsys")
    trend_response = await client_superuser.get(f"{base}/trend?code=bpsys")

    assert list_response.status_code == 200
    assert trend_response.status_code == 200
    assert len(trend_response.json()) == list_response.json()["total"]
