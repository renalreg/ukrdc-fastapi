from ukrdc_fastapi.config import configuration


def test_datahealth_multiple_ukrdcids(client):
    # Check expected links

    response = client.get(
        f"{configuration.base_url}/v1/admin/datahealth/multiple_ukrdcids"
    )
    assert response.status_code == 200

    multiple_id_groups = response.json().get("items")
    assert len(multiple_id_groups) == 1
    assert len(multiple_id_groups[0].get("records")) == 2
    assert {
        record.get("masterRecord").get("id")
        for record in multiple_id_groups[0].get("records")
    } == {1, 4}
