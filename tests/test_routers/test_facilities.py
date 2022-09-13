from ukrdc_fastapi.config import configuration

from ..utils import days_ago


async def test_facilities(client):
    response = await client.get(
        f"{configuration.base_url}/facilities?include_inactive=true"
    )
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


async def test_facility_detail(client):
    response = await client.get(
        f"{configuration.base_url}/facilities/TEST_SENDING_FACILITY_1"
    )
    json = response.json()
    assert json["id"] == "TEST_SENDING_FACILITY_1"


async def test_facility_error_history(client):
    response = await client.get(
        f"{configuration.base_url}/facilities/TEST_SENDING_FACILITY_1/error_history"
    )
    json = response.json()
    assert len(json) == 365
    assert json[-1].get("time") == days_ago(1).date().isoformat()


async def test_facility_patients_latest_errors(client):
    response = await client.get(
        f"{configuration.base_url}/facilities/TEST_SENDING_FACILITY_1/patients_latest_errors"
    )
    json = response.json()
    messages = json.get("items")

    assert len(messages) == 1
    assert messages[0].get("id") == 2


async def test_facility_stats_demographics(client):
    response = await client.get(
        f"{configuration.base_url}/facilities/TEST_SENDING_FACILITY_1/stats/demographics"
    )
    json = response.json()

    # Content tested in query submodule tests. Only care about the JSON response here
    assert len(json["ageDist"]) == 2
    assert len(json["genderDist"]) == 2
    assert len(json["ethnicityDist"]) == 1
