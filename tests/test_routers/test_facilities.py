from ukrdc_fastapi.config import configuration
from ..utils import days_ago


def test_facilities(client):
    response = client.get(f"{configuration.base_url}/v1/facilities/?include_empty=true")
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_facility_detail(client):
    response = client.get(
        f"{configuration.base_url}/v1/facilities/TEST_SENDING_FACILITY_1/"
    )
    json = response.json()
    assert json["id"] == "TEST_SENDING_FACILITY_1"
    assert json["statistics"]["lastUpdated"]


def test_facility_error_history(client):
    response = client.get(
        f"{configuration.base_url}/v1/facilities/TEST_SENDING_FACILITY_1/error_history/"
    )
    json = response.json()
    assert len(json) == 1
    assert json[0].get("time") == days_ago(1).date().isoformat()


def test_facility_patients_latest_errors(client):
    response = client.get(
        f"{configuration.base_url}/v1/facilities/TEST_SENDING_FACILITY_1/patients_latest_errors/"
    )
    json = response.json()
    messages = json.get("items")

    assert len(messages) == 1
    assert messages[0].get("id") == 3
