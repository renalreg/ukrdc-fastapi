def test_facilities(client):
    response = client.get("/api/facilities")
    ids = {item.get("id") for item in response.json()}
    assert ids == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
    }


def test_facility_detail(client):
    response = client.get("/api/facilities/TEST_SENDING_FACILITY_1")
    # NOTE: DISTINCT ON (used to calculate error stats) isn't supported by SQLite
    json = response.json()
    assert json["id"] == "TEST_SENDING_FACILITY_1"
    # Expect non-null values
    assert json["statistics"]["recordsWithErrors"] == 1
