from tests.utils import days_ago
from ukrdc_fastapi.config import configuration


def test_record_observations(client):
    response = client.get(
        f"{configuration.base_url}/v1/patientrecords/PYTEST01:PV:00000000A/observations"
    )
    assert response.status_code == 200
    assert {
        "enteredAt": None,
        "enteredAtDescription": None,
        "observationDesc": "OBSERVATION_SYS_1_DESC",
        "observationTime": days_ago(730).isoformat(),
        "observationUnits": "OBSERVATION_SYS_1_UNITS",
        "observationValue": "OBSERVATION_SYS_1_VALUE",
        "prePost": None,
    } in response.json()["items"]

    assert {
        "enteredAt": None,
        "enteredAtDescription": None,
        "observationDesc": "OBSERVATION_DIA_1_DESC",
        "observationTime": days_ago(730).isoformat(),
        "observationUnits": "OBSERVATION_DIA_1_UNITS",
        "observationValue": "OBSERVATION_DIA_1_VALUE",
        "prePost": None,
    } in response.json()["items"]

    assert {
        "enteredAt": None,
        "enteredAtDescription": None,
        "observationDesc": "OBSERVATION_DESC",
        "observationTime": days_ago(365).isoformat(),
        "observationUnits": "OBSERVATION_UNITS",
        "observationValue": "OBSERVATION_VALUE",
        "prePost": None,
    } in response.json()["items"]
