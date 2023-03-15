from ukrdc_fastapi.config import configuration

from ..utils import days_ago


async def test_facilities(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities?include_inactive=true"
    )
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TSF01",
    }


async def test_facilities_superuser(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/facilities?include_inactive=true"
    )
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TSF01",
        "TSF02",
    }


async def test_facility_detail(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF01"
    )
    json = response.json()
    assert json["id"] == "TSF01"


async def test_facility_detail_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF02"
    )
    assert response.status_code == 403


async def test_facility_error_history(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF01/error_history"
    )
    json = response.json()
    assert len(json) == 365
    assert json[-1].get("time") == days_ago(1).date().isoformat()


async def test_facility_error_history_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF02/error_history"
    )
    assert response.status_code == 403


async def test_facility_patients_latest_errors(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF01/patients_latest_errors"
    )
    json = response.json()
    messages = json.get("items")

    assert len(messages) == 1
    assert messages[0].get("id") == 2


async def test_facility_patients_latest_errors_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF02/patients_latest_errors"
    )
    assert response.status_code == 403


async def test_facility_stats_demographics(client_superuser):
    # Repeat to ensure cached response matches
    responses = set()
    for _ in range(2):
        response = await client_superuser.get(
            f"{configuration.base_url}/facilities/TSF01/stats/demographics"
        )
        assert response.status_code == 200
        responses.add(response.text)

    assert len(responses) == 1


async def test_facility_stats_demographics_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF02/stats/demographics"
    )
    assert response.status_code == 403


async def test_facility_stats_krt(client_superuser):
    # Repeat to ensure cached response matches
    responses = set()
    for _ in range(2):
        response = await client_superuser.get(
            f"{configuration.base_url}/facilities/TSF01/stats/krt"
        )
        assert response.status_code == 200
        responses.add(response.text)

    assert len(responses) == 1


async def test_facility_stats_krt_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/facilities/TSF02/stats/krt"
    )
    assert response.status_code == 403
