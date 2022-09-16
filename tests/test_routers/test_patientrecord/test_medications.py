from tests.utils import days_ago
from ukrdc_fastapi.config import configuration


async def test_record_medications(client):
    response = await client.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/medications"
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "fromTime": days_ago(730).isoformat(),
            "toTime": None,
            "drugProductGeneric": "DRUG_PRODUCT_GENERIC",
            "comment": None,
            "enteringOrganizationCode": None,
            "enteringOrganizationDescription": None,
        },
        {
            "fromTime": days_ago(730).isoformat(),
            "toTime": days_ago(-999).isoformat(),
            "drugProductGeneric": "DRUG_PRODUCT_GENERIC_2",
            "comment": None,
            "enteringOrganizationCode": None,
            "enteringOrganizationDescription": None,
        },
    ]
