from tests.utils import days_ago


def test_record_medications(client):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/medications")
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
