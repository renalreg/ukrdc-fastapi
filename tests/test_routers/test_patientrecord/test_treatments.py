from tests.utils import days_ago
from ukrdc_fastapi.config import configuration


async def test_record_treatments(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/treatments"
    )
    assert response.status_code == 200
    assert {
        "id": "TREATMENT1",
        "fromTime": days_ago(730).date().isoformat(),
        "toTime": None,
        "admitReasonCode": "1",
        "admitReasonCodeStd": None,
        "admitReasonDesc": None,
        "dischargeReasonCode": None,
        "dischargeReasonCodeStd": None,
        "dischargeReasonDesc": None,
        "healthCareFacilityCode": "TEST_SENDING_FACILITY_1",
    } in response.json()

    assert {
        "id": "TREATMENT2",
        "fromTime": days_ago(730).date().isoformat(),
        "toTime": days_ago(-999).date().isoformat(),
        "admitReasonCode": "1",
        "admitReasonCodeStd": None,
        "admitReasonDesc": None,
        "dischargeReasonCode": None,
        "dischargeReasonCodeStd": None,
        "dischargeReasonDesc": None,
        "healthCareFacilityCode": "TEST_SENDING_FACILITY_1",
    } in response.json()
